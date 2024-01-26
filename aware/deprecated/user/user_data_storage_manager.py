<import threading
from typing import Callable

from aware.memory.working_memory.data_storage_manager import DataStorageManager
from aware.memory.profiles.agent_profile import UserProfile
from aware.memory.memory_manager import MemoryManager
from aware.architecture.user.user_message import UserMessage
from aware.deprecated.chat import Chat
from aware.deprecated.conversation import Conversation
from aware.config.config import Config
from aware.utils.logger.file_logger import FileLogger


class UserDataStorageManager(DataStorageManager):
    def __init__(
        self,
        assistant_name: str,
        user_profile: UserProfile,
        context: str,
        memory_manager: MemoryManager,
        on_conversation_summary: Callable,
    ):
        self.user_profile = user_profile
        self.user_name = self.user_profile.get_name()
        self.assistant_name = assistant_name
        self.conversation = Conversation(
            module_name="user_data_storage_manager",
            model_name="gpt-4",
            should_trim=False,
        )
        self.conversation.add_system_message(message="This is the conversation:")
        self.conversation_timer = None

        self.logger = FileLogger("user_data_storage_manager", should_print=False)
        chat = Chat(
            module_name="user_data_storage_manager",
            logger=self.logger,
            system_prompt_kwargs={
                "user_name": self.user_name,
                "assistant_name": assistant_name,
                "user_profile": self.get_user_profile_str(),
                "context": context,
                "conversation": "",
            },
        )
        super().__init__(
            chat=chat,
            user_name=self.user_name,
            memory_manager=memory_manager,
            logger=self.logger,
            functions=[self.append_user_profile, self.edit_user_profile],
        )
        self.on_conversation_summary = on_conversation_summary
        self.context = context

    def add_message(self, message: UserMessage):
        self.conversation.add_user_message(
            message=message.message, user_name=message.user_name
        )
        if self.conversation.get_current_tokens() > Config().max_conversation_tokens:
            self.step()
        elif message.user_name == self.assistant_name:
            # Cancel the existing timer if it's running
            if (
                self.conversation_timer is not None
                and self.conversation_timer.is_alive()
            ):
                self.conversation_timer.cancel()

            # Create a new timer instance and start it
            self.conversation_timer = threading.Timer(
                Config().conversation_timeout_sec, self.step
            )
            self.conversation_timer.start()

    def append_user_profile(self, field: str, data: str):
        """
        Append data into a specific field of the user profile.

        Args:
            field (str): Field to edit.
            data (str): Data to be inserted.
        """
        return self.user_profile.insert_user_profile(field, data)

    def edit_user_profile(self, field: str, old_data: str, new_data: str):
        """
        Edit the user profile overwriting the old data with the new data.

        Args:
            field (str): Field to edit.
            old_data (str): Old data to be replaced.
            new_data (str): New data to replace the old data.
        """
        return self.user_profile.edit_user_profile(field, old_data, new_data)

    def stop(self, conversation_summary: str, potential_query: str):
        """Stop saving info. Call this function after all relevant data has been stored and provide a summary of the conversation.

        Args:
            conversation_summary (str): A summary of the conversation.
            potential_query (str): A potential query that might be used to find this conversation.
        """
        self.on_conversation_summary(conversation_summary, potential_query)
        return super().stop()

    def get_user_profile_str(self):
        return self.user_profile.to_string()

    def update_system(self):
        """Overrides agent update_system function to update the current system with updated user profile and context."""
        system_prompt_kwargs = {
            "user_name": self.user_name,
            "assistant_name": self.assistant_name,
            "user_profile": self.user_profile.to_string(),
            "context": self.context,
            "conversation": self.conversation.to_string(),
        }
        self.chat.edit_system_message(system_prompt_kwargs=system_prompt_kwargs)

    def update_context(self, context: str):
        self.context = context

    def step(self):
        """Store the data from current conversation and restart it"""
        self.run_agent()
        self.conversation.restart()
