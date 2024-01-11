import os
import threading

from aware.agent.memory.memory_manager import MemoryManager
from aware.agent.memory.user import (
    UserContextManager,
    UserThoughtGenerator,
    UserDataStorageManager,
)
from aware.agent.memory.user.user_profile import UserProfile
from aware.architecture.helpers.topics import (
    DEF_SEARCH_DATABASE,
    DEF_GET_THOUGHT,
)
from aware.architecture.user.user_message import UserMessage
from aware.config.config import Config
from aware.permanent_storage.permanent_storage import get_permanent_storage_path
from aware.utils.communication_protocols import Server
from aware.utils.json_manager import JSONManager
from aware.utils.logger.file_logger import FileLogger


class UserWorkingMemory:
    def __init__(self):
        self.assistant_name = Config().assistant_name
        path = os.path.join(
            get_permanent_storage_path(), "user_data", "user_profile.json"
        )
        self.user_profile = UserProfile(file_path=path)
        self.user_name = self.get_user_name()

        self.memory_manager = MemoryManager(
            user_name=self.user_name,
            logger=FileLogger("user_memory_manager", should_print=False),
        )

        self.data_storage_manager = UserDataStorageManager(
            assistant_name=self.assistant_name,
            user_profile=self.user_profile,
            memory_manager=self.memory_manager,
            on_conversation_summary=self.on_conversation_summary,
        )

        working_memory_path = os.path.join(
            get_permanent_storage_path(), "user_data", "working_memory.json"
        )
        json_manager = JSONManager(file_path=working_memory_path)
        self.context_manager = UserContextManager(
            assistant_name=self.assistant_name,
            user_name=self.user_name,
            user_profile=self.get_user_profile_str(),
            json_manager=json_manager,
        )
        self.context_manager_thread = threading.Thread(target=self.update_context)
        self.context_manager_thread.start()

        self.thought_generator = UserThoughtGenerator(
            assistant_name=self.assistant_name,
            user_name=self.user_name,
            context=self.get_context(),
            user_profile=self.get_user_profile_str(),
            memory_manager=self.memory_manager,
            logger=FileLogger("user_thought_generator", should_print=False),
            json_manager=json_manager,
        )
        self.thought_generator_thread = threading.Thread(target=self.generate_thought)
        # Thought Generator sync mechanisms to have both async and sync thought generation.
        self.pause_event = threading.Event()
        self.thought_ready_event = threading.Event()
        self.pause_condition = threading.Condition()
        self.is_paused = False

        self.thought_generator_thread.start()

        self.get_thought_server = Server(
            address=f"tcp://{Config().assistant_ip}:{Config().server_port}",
            topics=[f"{self.user_name}_{DEF_GET_THOUGHT}"],
            callback=self.get_thought_sync,
        )
        self.search_user_info_async_server = Server(
            address=f"tcp://{Config().assistant_ip}:{Config().server_port}",
            topics=[f"{self.user_name}_{DEF_SEARCH_DATABASE}"],
            callback=self.search_user_info,
        )

    def add_message(self, message: UserMessage):
        self.context_manager.add_message(message)
        self.thought_generator.add_message(message)
        self.data_storage_manager.add_message(message)

    def generate_thought(self):
        while True:
            default_execution = False
            with self.pause_condition:
                if self.pause_event.is_set():
                    self.is_paused = True
                    self.pause_condition.notify_all()  # Notify that it's paused
                    self.pause_event.clear()  # Clear the event to resume later
                    self.pause_condition.wait()  # Wait to be notified to resume
                    default_execution = True
                self.is_paused = False

            self.thought_generator.edit_system(
                user_profile=self.get_user_profile_str(), context=self.get_context()
            )
            self.thought_generator.step(default_execution=default_execution)

            if default_execution:
                # Only signal that a thought is ready if this iteration was for a specific request
                self.thought_ready_event.set()

    def get_thought_sync(self, query: str):
        self.pause_event.set()  # Signal to pause generate_thought

        with self.pause_condition:
            while not self.is_paused:
                self.pause_condition.wait()  # Wait until generate_thought is paused

        search_message = f"I want to find information about: {query}, please memory manager, provide me a thought."
        self.thought_generator.add_message(
            UserMessage(user_name=Config().assistant_name, message=search_message)
        )

        # Notify generate_thought to resume
        with self.pause_condition:
            self.pause_condition.notify_all()

        self.thought_ready_event.wait()  # Wait until the thought is ready
        self.thought_ready_event.clear()  # Reset the event for future use

        return f"Info found: {self.thought_generator.get_thought()}"

    def get_context(self):
        return self.context_manager.get_context()

    def get_thought(self):
        return self.thought_generator.get_thought()

    def get_user_profile_str(self):
        return self.data_storage_manager.get_user_profile_str()

    def get_user_name(self):
        user_name = self.user_profile.get_name()
        if not user_name:
            user_name = input("Please introduce your name: ")
            self.user_profile.insert_user_profile("name", user_name)
        return user_name

    def search_user_info(self, query: str):
        """Creates a dispensable thought generator to search for information about the query.

        Args:
            query (str): Query to search for.
        """

        search_message = f"I want to find this info: '{query}' from {self.user_name}. Please thought generator, first check the user profile, if not found, then search in the database."
        dispensable_thought_generator = UserThoughtGenerator(
            assistant_name=self.assistant_name,
            user_name=self.user_name,
            context=self.get_context(),
            user_profile=self.get_user_profile_str(),
            memory_manager=self.memory_manager,
            logger=FileLogger("search_user_info", should_print=False),
        )
        dispensable_thought_generator.add_message(
            UserMessage(user_name=Config().assistant_name, message=search_message)
        )
        dispensable_thought_generator.step(default_execution=True)
        return f"Info found: {dispensable_thought_generator.get_thought()}"

    def on_conversation_summary(self, summary: str, potential_query: str):
        self.context_manager.summarize_context(summary)
        self.memory_manager.store_conversation(summary, potential_query)

    def update_context(self):
        while True:
            self.context_manager.edit_system(
                user_profile=self.get_user_profile_str(), context=self.get_context()
            )
            self.context_manager.step()
