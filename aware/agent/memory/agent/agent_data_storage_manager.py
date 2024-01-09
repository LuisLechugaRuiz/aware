import threading

from aware.agent.memory.working_memory.data_storage_manager import DataStorageManager
from aware.architecture.user.user_message import UserMessage
from aware.chat.chat import Chat
from aware.chat.conversation import Conversation
from aware.config.config import Config
from aware.utils.logger.file_logger import FileLogger


class AgentDataStorageManager(DataStorageManager):
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.conversation = Conversation(
            module_name="agent_data_storage_manager",
            model_name="gpt-4",
            should_trim=False,
        )
        self.conversation.add_system_message(message="This is the conversation:")
        self.conversation_timer = None

        self.logger = FileLogger("agent_data_storage_manager", should_print=False)
        chat = Chat(
            module_name="agent_data_storage_manager",
            logger=self.logger,
            system_prompt_kwargs={
                "agent_name": agent_name,
                "conversation": "",
            },
        )
        # TODO: Should we add an "Open format" profile for each agent? This way the model can define fields and update them?
        # TODO: Can this function store info directly at user data? I don't think so...
        super().__init__(
            chat=chat,
            user_name=agent_name,
            logger=self.logger,
            functions=[],
        )

    def add_message(self, message: UserMessage):
        self.conversation.add_user_message(
            message=message.message, user_name=message.user_name
        )
        if self.conversation.get_current_tokens() > Config().max_conversation_tokens:
            self.step()
        else:
            # Cancel the existing timer if it's running
            if (
                self.conversation_timer is not None
                and self.conversation_timer.is_alive()
            ):
                self.conversation_timer.cancel()

            # Create a new timer instance and start it
            self.conversation_timer = threading.Timer(
                Config().task_timeout_sec, self.step
            )
            self.conversation_timer.start()

    def update_system(self):
        """Overrides agent update_system function to update the current system with updated user profile and context."""
        system_prompt_kwargs = {
            "user_name": self.user_name,
            "agent_name": self.agent_name,
            "conversation": self.conversation.to_string(),
        }
        self.chat.edit_system_message(system_prompt_kwargs=system_prompt_kwargs)

    def step(self):
        """Store the data from current conversation and restart it"""
        self.run_agent()
        self.conversation.restart()
