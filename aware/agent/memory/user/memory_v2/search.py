import json
from openai.types.chat.chat_completion_message_tool_call_param import (
    ChatCompletionMessageToolCallParam,
    Function,
)
import os
from queue import Queue
import threading
from time import sleep
from typing import List
import uuid

from aware.agent.memory.memory_manager import MemoryManager
from aware.agent.memory.user.user_profile import UserProfile
from aware.architecture.helpers.topics import (
    DEF_SEARCH_DATABASE,
)
from aware.config.config import Config
from aware.chat.chat import Chat
from aware.architecture.user.user_message import UserMessage
from aware.utils.communication_protocols import Server
from aware.utils.logger.file_logger import FileLogger
from aware.permanent_storage.permanent_storage import get_permanent_storage_path


DEF_CONVERSATION_TIMEOUT = 500  # TODO: MOVE TO CONFIG
DEF_DEFAULT_EMPTY_CONTEXT = "No context yet, please update it."


# Requires two processes:
# 1. Update the context -> After every new assistant message.
# 2. Update the thought -> After every new user message.


class UserSearch(MemoryManager):
    def __init__(self):
        path = os.path.join(
            get_permanent_storage_path(), "user_data", "user_profile.json"
        )
        self.user_profile = UserProfile(file_path=path)
        self.messages_queue: Queue[UserMessage] = Queue()

        self.context_update_thread = threading.Thread(target=self.update_context)
        self.context_update_thread.start()
        # TODO: Both stops the agent, it should be a single call and stop.
        self.context_update_functions = [
            self.append_context,
            self.edit_context,
        ]

        self.thought_generation_thread = threading.Thread(target=self.generate_thought)
        self.thought_generation_thread.start()
        self.thought_generation_functions = [
            # TODO: Include manager search.
            self.search
            self.intermediate_thought,
            self.final_thought,
        ]

        self.conversation_timer = None
        self.thought = ""
        self.context = DEF_DEFAULT_EMPTY_CONTEXT

        self.conversation_functions = [
            self.append_context,
            self.edit_context,
            self.append_user_profile,
            self.edit_user_profile,
            self.transmit_insight,
            self.wait_for_user,
        ]

        # TODO: use user_id.
        register = self.register_user()
        user_name = self.get_name()
        self.assistant_name = f"{Config().assistant_name}_memory_manager"
        super().__init__(
            user_name=user_name,
            chat=Chat(
                module_name="user_memory_manager",
                logger=FileLogger("user_memory_manager", should_print=False),
                system_prompt_kwargs={
                    "user_name": user_name,
                    "assistant_name": Config().assistant_name,
                    "user_profile": self.user_profile.to_string(),
                    "context": "No context yet, please update me.",
                    "conversation_warning_threshold": False,
                    "conversation_remaining_tokens": Config().max_conversation_tokens,
                },
                assistant_name=self.assistant_name,
                api_key=Config().openai_memory_api_key,
            ),
            functions=self.conversation_functions,
            logger=FileLogger("user_memory_manager", should_print=False),
        )
        if register:
            self.create_user(name=user_name)

        self.search_user_info_server = Server(
            address=f"tcp://{Config().assistant_ip}:{Config().server_port}",
            topics=[f"{self.user_name}_{DEF_SEARCH_DATABASE}"],
            callback=self.search_user_info,
        )

    def get_name(self):
        return self.user_profile.get_name()

    def register_user(self):
        user_name = self.get_name()
        if not user_name:
            user_name = input("Please introduce your name: ")
            self.save_name(user_name)
            return True
        return False

    def save_name(self, name: str):
        self.user_profile.insert_user_profile("name", name)

    def add_message(self, message: UserMessage):
        self.messages_queue.put(message)

    def search_user_info(self, query: str):
        search_message = f"I want to find information about: {query}, please memory manager, provide me a thought."
        self.chat.conversation.add_user_message(
            search_message, user_name=Config().assistant_name
        )

        # WAIT FOR THOUGHT -> TODO: ADD THIS BETTER WITH TIMEOUT
        if not self.running:
            self.run_agent()
        else:
            old_thought = self.thought
            while old_thought == self.thought:
                sleep(0.1)

        return f"Info found: {self.thought}"

    def update_system(self):
        """Override the default update system to add the user profile and context."""

        remaining_tokens, should_trigger_warning = self.chat.get_remaining_tokens()
        system_prompt_kwargs = {
            "user_name": self.user_name,
            "assistant_name": Config().assistant_name,
            "user_profile": self.user_profile.to_string(),
            "context": self.get_context(),
            "conversation_warning_threshold": should_trigger_warning,
            "conversation_remaining_tokens": remaining_tokens,
        }
        self.chat.edit_system_message(system_prompt_kwargs=system_prompt_kwargs)

    # TODO: ADJUST! WE CAN'T SAVE AN INTERACTION FROM USER_MEMORY_MANAGER AT CONVERSATION AS IT WILL BREAK LOGIC. SAVE CHAT AS THOUGHT!!
    def run_memory_agent(self):
        while True:
            # Empty the queue - Add user and assistant messages.
            is_assistant_message = False
            # Wait for next user message. TODO: WAIT FOR USER AND THEN SYSTEM (TO ENABLE CHAT WHERE MULTIPLE USERS CAN INTERACT).
            while not is_assistant_message:
                if not self.messages_queue.empty():
                    message = self.messages_queue.get()

                    self.chat.conversation.add_user_message(
                        message.message, user_name=message.user_name
                    )
                    is_assistant_message = message.user_name == Config().assistant_name
                    if is_assistant_message:
                        # Cancel the existing timer if it's running
                        if (
                            self.conversation_timer is not None
                            and self.conversation_timer.is_alive()
                        ):
                            self.conversation_timer.cancel()

                        # Create a new timer instance and start it
                        self.conversation_timer = threading.Timer(
                            DEF_CONVERSATION_TIMEOUT, self.on_conversation_finished
                        )
                        self.conversation_timer.start()

                    self.messages_queue.task_done()
            self.run_agent(default_tool_calls=self.create_default_tool_calls)

    def get_context(self):
        # TODO: Make this thread safe.

        if self.context is None:
            conversation_summary = self.weaviate_db.get_last_conversation_summary()
            if conversation_summary.error is None:
                self.context = conversation_summary.data
            else:
                self.context = ""

        return self.context

    def create_default_tool_calls(self, insight: str):
        """Create a tool call as if the agent was calling transmit_insight when it answer by string to avoid appending it to conversation"""
        tool_calls: List[ChatCompletionMessageToolCallParam] = [
            ChatCompletionMessageToolCallParam(
                id=uuid.uuid4(),
                function=Function(
                    arguments=json.dumps({"insight": insight}), name="transmit_insight"
                ),
                name="transmit_insight",
            )
        ]
        return tool_calls

    # TODO: THIS CONVERSATION SHOULD BE CALLED ON CONVERSATION FINISHES OR AFTER X AMOUNT OF TOKENS TO STORE A PERMANENT SUMMARY (THE CONTEXT)
    def on_conversation_finished(self):
        """
        Store the summary of the conversation in the database.
        """
        # print(
        #     "CONVERSATION FINISHED, NOW I SHOULD ASK THE LLM TO PROVIDE A POTENTIAL QUERY BEFORE SAVING!"
        # )
        # potential_query = input(
        #     "DEBUGGING, ADD A POTENTIAL QUERY: "
        # )  # TODO: ASK THE AGENT.
        # result = self.weaviate_db.store_conversation(
        #     user_name=self.user_name,
        #     summary=self.get_context(),
        #     potential_query=potential_query,
        # )
        # return result
        pass

    def edit_user_profile(self, field: str, old_data: str, new_data: str):
        """
        Edit the user profile overwriting the old data with the new data.

        Args:
            field (str): Field to edit.
            old_data (str): Old data to be replaced.
            new_data (str): New data to replace the old data.
        """
        return self.user_profile.edit_user_profile(field, old_data, new_data)

    def append_user_profile(self, field: str, data: str):
        """
        Append data into a specific field of the user profile.

        Args:
            field (str): Field to edit.
            data (str): Data to be inserted.
        """
        return self.user_profile.insert_user_profile(field, data)

    def wait_for_user(self):
        """
        Pauses operations, awaiting the next user input before proceeding.
        """
        self.stop_agent()
        return "Waiting for user's input..."

    def search_conversation(self, query: str):
        """
        Search for a specific query in the conversation.

        Args:
            query (str): Query to search for.
        """
        return self.weaviate_db.search_conversation(query)

    def edit_context(self, old_data: str, new_data: str):
        """
        Edit the assistant's context overwriting the old context with the new context.

        Args:
            old_data (str): Old data that should be replaced.
            new_data (str): New data to replace the old data.
        """
        # TODO: Make this thread safe.
        try:
            self.context.replace(old_data, new_data)
            return "Context edited."
        except Exception as e:
            return f"Error while editing context: {e}"

    def append_context(self, data: str):
        """
        Append data at the end of the assistant's context.

        Args:
            data (str): Data to be appended.
        """
        if self.context == DEF_DEFAULT_EMPTY_CONTEXT:
            self.context = ""
        # TODO: Make this thread safe.
        self.context += data
        return "Context appended."

    def transmit_insight(self, insight: str):
        """
        Crafts a strategic insight in the first person, as if it's the assistant's own thought.
        This insight is intended to optimize the assistant's performance in their next interaction with the user.

        Args:
            insight (str): A strategic insight or piece of advice, phrased as if it's the assistant's own thought.
        """
        self.thought = insight
        self.stop_agent()  # TODO: Define if we should stop after thinking.
        return "Insight transmitted."
