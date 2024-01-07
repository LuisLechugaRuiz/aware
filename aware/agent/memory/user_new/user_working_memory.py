import os
import threading
from time import sleep

from aware.agent.memory.user.user_profile import UserProfile
from aware.architecture.helpers.topics import (
    DEF_SEARCH_DATABASE,
)
from aware.config.config import Config
from aware.architecture.user.user_message import UserMessage
from aware.utils.communication_protocols import Server
from aware.permanent_storage.permanent_storage import get_permanent_storage_path


from aware.agent.memory.user_new import UserContextManager, UserThoughtGenerator

DEF_CONVERSATION_TIMEOUT = (
    500  # TODO: MOVE TO CONFIG AND USE IT FOR STORING (TIMEOUT AND MAX LENGTH)
)
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

        # TODO: use user_id.
        self.register_user()
        self.user_name = self.user_profile.get_name()

        # TODO: RETRIEVE INITIAL CONTEXT FROM JSON - ANOTHER JSON FOR USER WORKING MEMORY.
        self.context_manager = UserContextManager(
            assistant_name=Config().assistant_name,
            user_name=self.user_name,
            user_profile=self.user_profile.to_string(),
            initial_context="",
        )
        self.context_manager_thread = threading.Thread(target=self.update_context)
        self.context_manager_thread.start()

        self.thought_generator = UserThoughtGenerator(
            assistant_name=Config().assistant_name,
            user_name=self.user_name,
            initial_thought="",  # TODO: GET FROM JSON
            user_profile=self.user_profile.to_string(),
            context="",  # TODO: GET FROM JSON
        )
        self.thought_generator_thread = threading.Thread(target=self.generate_thought)
        self.thought_generator_thread.start()

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
        self.context_manager.add_message(message)
        self.thought_generator.add_message(message)

    def search_user_info(self, query: str):
        search_message = f"I want to find information about: {query}, please memory manager, provide me a thought."
        self.thought_generator.add_message(
            UserMessage(user_name=Config().assistant_name, message=search_message)
        )

        # WAIT FOR THOUGHT -> TODO: ADD THIS BETTER WITH TIMEOUT
        old_thought = self.get_thought()
        while old_thought == self.get_thought():
            sleep(0.1)

        return f"Info found: {self.get_thought()}"

    def update_context(self):
        while True:
            self.context_manager.edit_system(
                user_profile=self.user_profile.to_string(), context=self.get_context()
            )
            self.context_manager.step()

    def generate_thought(self):
        while True:
            self.thought_generator.edit_system(
                user_profile=self.user_profile.to_string(), context=self.get_context()
            )
            self.thought_generator.step()

    def get_context(self):
        return self.context_manager.get_context()

    def get_thought(self):
        return self.thought_generator.get_thought()
