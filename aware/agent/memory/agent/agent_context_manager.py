from queue import Queue

from aware.agent.memory.working_memory import ContextManager
from aware.architecture.user.user_message import UserMessage
from aware.chat.chat import Chat
from aware.utils.logger.file_logger import FileLogger


# TODO: Create system memory: It should be similar to User but with modifications:
# - In this case we are not optimizing for user conversation.
# - We don't have user profile.
# - We need to create the context from Tool Execution and not just User Message, we need to extract ALL new messages at conversation...
class AgentContextManager(ContextManager):
    def __init__(
        self,
        agent_name: str,
        initial_context: str,
    ):
        self.logger = FileLogger("agent_context_manager", should_print=False)
        chat = Chat(
            module_name="agent_context_manager",
            logger=self.logger,
            system_prompt_kwargs={
                "agent_name": agent_name,
                "context": initial_context,
            },
        )
        self.messages_queue: Queue[UserMessage] = Queue()
        self.agent_name = agent_name

        super().__init__(chat=chat, initial_context=initial_context, logger=self.logger)

    # TODO: add_message should count the tools... in this case is not UserMessage, needs rethinking.
    def add_message(self, message: UserMessage):
        self.messages_queue.put(message)

    def edit_system(self, context: str):
        """Override the default update system to add the user profile and context."""

        remaining_tokens, should_trigger_warning = self.chat.get_remaining_tokens()
        system_prompt_kwargs = {
            "agent_name": self.agent_name,
            "context": context,
            "conversation_warning_threshold": should_trigger_warning,
            "conversation_remaining_tokens": remaining_tokens,
        }
        self.chat.edit_system_message(system_prompt_kwargs=system_prompt_kwargs)

    def step(self):
        """Run a single step to update the context on new assistant messages"""

        if not self.messages_queue.empty():
            while not self.messages_queue.empty():
                message = self.messages_queue.get()
                self.chat.conversation.add_user_message(
                    message.message, user_name=message.user_name
                )
                self.messages_queue.task_done()
        self.run_agent()
