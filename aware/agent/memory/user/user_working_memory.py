import threading
from time import sleep

from aware.agent.memory.user import (
    UserContextManager,
    UserThoughtGenerator,
    UserDataStorageManager,
)
from aware.architecture.helpers.topics import (
    DEF_SEARCH_DATABASE,
)
from aware.config.config import Config
from aware.architecture.user.user_message import UserMessage
from aware.utils.communication_protocols import Server


class UserWorkingMemory:
    def __init__(self):
        self.assistant_name = Config().assistant_name
        self.data_storage_manager = UserDataStorageManager(
            assistant_name=self.assistant_name
        )
        self.user_name = self.data_storage_manager.get_user_name()

        # TODO: RETRIEVE INITIAL CONTEXT FROM JSON - ANOTHER JSON FOR USER WORKING MEMORY.
        self.context_manager = UserContextManager(
            assistant_name=self.assistant_name,
            user_name=self.user_name,
            user_profile=self.get_user_profile_str(),
            initial_context="",
        )
        self.context_manager_thread = threading.Thread(target=self.update_context)
        self.context_manager_thread.start()

        self.thought_generator = UserThoughtGenerator(
            assistant_name=self.assistant_name,
            user_name=self.user_name,
            initial_thought="",  # TODO: GET FROM JSON
            user_profile=self.get_user_profile_str(),
            context="",  # TODO: GET FROM JSON
        )
        self.thought_generator_thread = threading.Thread(target=self.generate_thought)
        self.thought_generator_thread.start()

        self.search_user_info_server = Server(
            address=f"tcp://{Config().assistant_ip}:{Config().server_port}",
            topics=[f"{self.user_name}_{DEF_SEARCH_DATABASE}"],
            callback=self.search_user_info,
        )

    def add_message(self, message: UserMessage):
        self.context_manager.add_message(message)
        self.thought_generator.add_message(message)
        self.data_storage_manager.add_message(message)

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
                user_profile=self.get_user_profile_str(), context=self.get_context()
            )
            self.context_manager.step()

    def generate_thought(self):
        while True:
            self.thought_generator.edit_system(
                user_profile=self.get_user_profile_str(), context=self.get_context()
            )
            self.thought_generator.step()

    def get_context(self):
        return self.context_manager.get_context()

    def get_thought(self):
        return self.thought_generator.get_thought()

    def get_user_profile_str(self):
        return self.data_storage_manager.get_user_profile_str()

    def get_user_name(self):
        return self.user_name
