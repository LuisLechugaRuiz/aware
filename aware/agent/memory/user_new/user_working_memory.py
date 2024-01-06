import os
from queue import Queue
import threading
from time import sleep

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


from aware.agent.memory.user_new import UserContextUpdate, UserThoughtGeneration

DEF_CONVERSATION_TIMEOUT = 500  # TODO: MOVE TO CONFIG
DEF_DEFAULT_EMPTY_CONTEXT = "No context yet, please update it."


# Requires two processes:
# 1. Update the context -> After every new assistant message.
# 2. Update the thought -> After every new user message.


class UserWorkingMemory:
    def __init__(self):
        path = os.path.join(
            get_permanent_storage_path(), "user_data", "user_profile.json"
        )
        self.user_profile = UserProfile(file_path=path)

        # TODO: WE NEED TWO QUEUES -> ONE FOR THOUGHT AND ANOTHER ONE FOR CONTEXT!!!
        self.messages_queue: Queue[UserMessage] = Queue()

        # TODO: RETRIEVE INITIAL CONTEXT FROM JSON - ANOTHER JSON FOR USER WORKING MEMORY.
        self.context_update = UserContextUpdate()
        self.context_update_thread = threading.Thread(
            target=self.context_update.run
        )  # TODO: IMPLEMENT RUN BASED ON CONTEXT_UPDATE FUNC
        self.context_update_thread.start()

        # TODO: use user_id.
        self.register_user()
        self.user_name = self.user_profile.get_name()
        self.thought_generation = UserThoughtGeneration(
            assistant_name=Config().assistant_name,
            user_name=self.user_name,
            initial_thought="",  # TODO: GET FROM JSON
            user_profile=self.user_profile.to_string(),
            context="",  # TODO: GET FROM JSON
        )
        self.thought_generation_thread = threading.Thread(
            target=self.thought_generation.run
        )
        self.thought_generation_thread.start()

        # TODO: REMOVE?!!
        self.assistant_name = f"{Config().assistant_name}_memory_manager"
        super().__init__(
            user_name=self.user_name,
            chat=Chat(
                module_name="user_memory_manager",
                logger=FileLogger("user_memory_manager", should_print=False),
                system_prompt_kwargs={
                    "user_name": self.user_name,
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

        # TODO: THIS SHOULD WAIT UNTIL THOUGHT GENERATION?
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

    def update_context(self):
        while True:
            # Empty the queue - Add user and assistant messages.
            is_assistant_message = False
            # Wait for next user message. TODO: WAIT FOR USER AND THEN SYSTEM (TO ENABLE CHAT WHERE MULTIPLE USERS CAN INTERACT).
            while not is_assistant_message:
                if not self.messages_queue.empty():
                    message = self.messages_queue.get()

                    self.context_update.chat.conversation.add_user_message(
                        message.message, user_name=message.user_name
                    )
                    is_assistant_message = message.user_name == Config().assistant_name
            self.context_update.run_agent()

    def generate_thought(self):
        while True:
            # Empty the queue - Add user and assistant messages.
            is_user_message = False
            while not is_user_message:
                if not self.messages_queue.empty():
                    message = self.messages_queue.get()
                    self.thought_generation.chat.conversation.add_user_message(
                        message.message, user_name=message.user_name
                    )
                    is_user_message = message.user_name == self.user_name
            self.thought_generation.run_agent()

    def on_user_profile_update(self, user_profile: dict):
        self.user_profile.update_user_profile(user_profile)

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
        return self.context_update.get_context()

    def get_thought(self):
        return self.thought_generation.get_thought()
