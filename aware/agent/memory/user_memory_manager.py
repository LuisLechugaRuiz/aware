import os
from pathlib import Path
from queue import Queue
import threading
from time import sleep

from aware.agent.memory.memory_manager import MemoryManager
from aware.agent.memory.user_profile import UserProfile
from aware.architecture.helpers.topics import (
    DEF_SEARCH_DATABASE,
)
from aware.architecture.helpers.tmp_ips import (
    DEF_ASSISTANT_IP,
    DEF_SERVER_PORT,
)
from aware.config.config import Config
from aware.chat.chat import Chat
from aware.chat.conversation import Conversation
from aware.architecture.user.user_message import UserMessage
from aware.utils.communication_protocols import Server
from aware.utils.logger.file_logger import FileLogger
from aware.permanent_storage.permanent_storage import get_permanent_storage_path


DEF_CONVERSATION_TIMEOUT = 500  # TODO: MOVE TO CONFIG
DEF_DEFAULT_EMPTY_CONTEXT = "No context yet, please update it."


class UserMemoryManager(MemoryManager):
    def __init__(self):
        path = os.path.join(
            get_permanent_storage_path(), "user_data", "user_profile.json"
        )
        self.user_profile = UserProfile(file_path=path)
        self.messages_queue: Queue[UserMessage] = Queue()

        self.run_thread = threading.Thread(target=self.run_memory_agent)
        self.run_thread.start()
        self.conversation_timer = None
        self.thought = ""
        self.context = DEF_DEFAULT_EMPTY_CONTEXT

        # TODO: ADAPT FUNCTIONS - THIS AGENT WILL RUN TWO DIFFERENT EXECUTIONS:
        # 1 - SAVE INFO FROM A CONVERSATION - MEANS UPDATING USER PROFILE IF NEEDED.
        # 2 - SEARCH FOR INFO - MEANS RUNNING THE AGENT AND WAITING FOR THE RESPONSE - WILL BE CALLED BY THE ASSISTANT.
        self.conversation_functions = [
            self.append_context,
            self.edit_context,
            self.edit_user_profile,
            self.insert_user_profile,
            self.think,
            self.wait_for_user,
        ]

        # TODO: use user_id.
        register = self.register_user()
        user_name = self.get_name()
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
                assistant_name=f"{Config().assistant_name}_memory_manager",
            ),
            functions=self.conversation_functions,
            logger=FileLogger("user_memory_manager", should_print=False),
        )
        if register:
            self.create_user(name=user_name)

        # TODO: Handle this properly, should we search for info at any category or run the agent?? !!
        # ON NEW MESSAGE JUST ADD IT AS USER FOR OUR AGENT AND WAIT FOR THE RESPONSE!!!!
        self.search_user_info_server = Server(
            address=f"tcp://{DEF_ASSISTANT_IP}:{DEF_SERVER_PORT}",
            topics=[f"{self.user_name}_{DEF_SEARCH_DATABASE}"],
            callback=self.search_user_info,  # TODO: START AGENT AND WAIT FOR RESPONSE!!
        )
        # TODO: Get by user_name?

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

    def search_user_info(self, message: UserMessage):
        # TODO: HERE WE SHOULD RUN THE AGENT ASKING HIM TO PROVIDE SPECIFIC INFO. APPEND NEW FUNCTION: ANSWER TO USER, SHOULD WE REMOVE THE DEFAULT ONES WHILE ON WAITING FOR ANSWER?
        # ONCE THE AGENT CALLS THE RESPONSE_TO_USER WE JUST SEND THE ANSWER BACK AND GIVE BACK THE NORMAL TOOLS.
        # THIS INVOLVES INTERRUPTING THE AGENT? OR SPAWNING A NEW ONE?
        return "User info retrieval not implemented yet, next iteration you will receive data."

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

    def run_memory_agent(self):
        while True:
            # Empty the queue - Add user and assistant messages.
            is_assistant_message = False
            # Wait for next user message.
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
            message = self.run_agent()
            if message:
                self.logger.info(f"Agent finished with message: {message}")

    def get_context(self):
        # TODO: Make this thread safe.

        if self.context is None:
            conversation_summary = self.weaviate_db.get_last_conversation_summary()
            if conversation_summary.error is None:
                self.context = conversation_summary.data
            else:
                self.context = ""

        return self.context

    # TODO: THIS CONVERSATION SHOULD BE CALLED ON CONVERSATION FINISHES OR AFTER X AMOUNT OF TOKENS TO STORE A PERMANENT SUMMARY (THE CONTEXT)
    def on_conversation_finished(self):
        """
        Store the summary of the conversation in the database.

        Returns:
            str: Feedback message.
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

        Returns:
            str: Feedback message.
        """
        return self.user_profile.edit_user_profile(field, old_data, new_data)

    def insert_user_profile(self, field: str, data: str):
        """
        Insert data into a specific field of the user profile.

        Args:
            field (str): Field to edit.
            data (str): Data to be inserted.

        Returns:
            str: Feedback message.
        """
        return self.user_profile.insert_user_profile(field, data)

    def wait_for_user(self):
        """
        Pauses operations, awaiting the next user input before proceeding.

        Returns:
            str: Feedback message.
        """
        self.stop_agent()
        return "Stopped."

    def search_conversation(self, query: str):
        """
        Search for a specific query in the conversation.

        Args:
            query (str): Query to search for.

        Returns:
            str: Feedback message.
        """
        return self.weaviate_db.search_conversation(query)

    def edit_context(self, old_data: str, new_data: str):
        """
        Edit the assistant's context overwriting the old context with the new context.

        Args:
            old_data (str): Old data that should be replaced.
            new_data (str): New data to replace the old data.

        Returns:
            str: Feedback message.
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

        Returns:
            str: Feedback message.
        """
        if self.context == DEF_DEFAULT_EMPTY_CONTEXT:
            self.context = ""
        # TODO: Make this thread safe.
        self.context += data
        return "Context appended."

    def think(self, thought: str):
        """
        Transmits a thought to the user, aiding in optimizing the user's performance.

        Returns:
            str: Feedback message.
        """
        print(f"Thought: {thought}")
        self.thought = thought
        self.stop_agent()  # TODO: Define if we should stop after thinking.
        return "Thought transmitted."
