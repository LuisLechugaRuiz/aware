from queue import Queue

from aware.agent.memory.working_memory import ContextManager
from aware.architecture.user.user_message import UserMessage
from aware.chat.chat import Chat
from aware.utils.json_manager import JSONManager
from aware.utils.logger.file_logger import FileLogger


class UserContextManager(ContextManager):
    def __init__(
        self,
        assistant_name: str,
        user_name: str,
        user_profile: str,
        json_manager: JSONManager,
    ):
        self.logger = FileLogger("user_context_manager", should_print=False)
        chat = Chat(
            module_name="user_context_manager",
            logger=self.logger,
            system_prompt_kwargs={
                "user_name": user_name,
                "assistant_name": assistant_name,
                "user_profile": user_profile,
                "context": "",
            },
        )
        self.messages_queue: Queue[UserMessage] = Queue()
        self.user_name = user_name
        self.assistant_name = assistant_name

        super().__init__(chat=chat, logger=self.logger, json_manager=json_manager)

    def add_message(self, message: UserMessage):
        self.messages_queue.put(message)

    def edit_system(self, user_profile: str, context: str):
        """Override the default update system to add the user profile and context."""

        remaining_tokens, should_trigger_warning = self.chat.get_remaining_tokens()
        system_prompt_kwargs = {
            "user_name": self.user_name,
            "assistant_name": self.assistant_name,
            "user_profile": user_profile,
            "context": context,
            "conversation_warning_threshold": should_trigger_warning,
            "conversation_remaining_tokens": remaining_tokens,
        }
        self.chat.edit_system_message(system_prompt_kwargs=system_prompt_kwargs)

    def step(self):
        """Run a single step to update the context on new assistant messages"""

        if not self.messages_queue.empty():
            is_assistant_message = False
            # Add the queue messages to the conversation.
            while not self.messages_queue.empty():
                message = self.messages_queue.get()
                self.chat.conversation.add_user_message(
                    message.message, user_name=message.user_name
                )
                is_assistant_message = message.user_name == self.assistant_name
                self.messages_queue.task_done()
            if is_assistant_message:
                self.run_agent()
                return self.get_context()
        return None
