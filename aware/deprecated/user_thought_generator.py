from queue import Queue
from typing import Optional

from aware.memory.memory_manager import MemoryManager
from aware.memory.working_memory import ThoughtGenerator
from aware.architecture.user.user_message import UserMessage
from aware.deprecated.chat import Chat
from aware.utils.json_manager import JSONManager
from aware.utils.logger.file_logger import FileLogger


class UserThoughtGenerator(ThoughtGenerator):
    def __init__(
        self,
        assistant_name: str,
        user_name: str,
        context: str,
        user_profile: str,
        memory_manager: MemoryManager,
        logger: FileLogger,
        json_manager: Optional[JSONManager] = None,
    ):
        self.assistant_name = assistant_name
        self.user_name = user_name
        self.messages_queue: Queue[UserMessage] = Queue()
        self.logger = logger
        chat = Chat(
            module_name="user_thought_generator",
            logger=self.logger,
            system_prompt_kwargs={
                "user_name": self.user_name,
                "assistant_name": self.assistant_name,
                "user_profile": user_profile,
                "context": context,
            },
        )

        super().__init__(
            chat=chat,
            user_name=user_name,
            memory_manager=memory_manager,
            logger=self.logger,
            json_manager=json_manager,
        )

    def add_message(self, message: UserMessage):
        self.messages_queue.put(message)

    def edit_system(self, user_profile: str, context: str):
        """Override current system with updated user profile and context."""
        system_prompt_kwargs = {
            "user_name": self.user_name,
            "assistant_name": self.assistant_name,
            "user_profile": user_profile,
            "context": context,
        }
        self.chat.edit_system_message(system_prompt_kwargs=system_prompt_kwargs)

    def step(self, default_execution: bool = False):
        """Run a single agent step to generate a new thought integrating new info from memory based on current conversation."""

        if not self.messages_queue.empty():
            is_user_message = False
            # Add the queue messages to the conversation.
            while not self.messages_queue.empty():
                message = self.messages_queue.get()
                self.chat.conversation.add_user_message(
                    message.message, user_name=message.user_name
                )
                is_user_message = message.user_name == self.user_name
                self.messages_queue.task_done()
            if default_execution:
                self.run_agent()
            elif is_user_message:
                self.run_agent()
