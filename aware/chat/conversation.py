from aware.chat.database.chat_database_handler import ChatDatabaseHandler
from aware.config.config import Config
from aware.data.data_saver import DataSaver  # TODO: Refactor it to save traces.
from aware.utils.helpers import count_message_tokens

from aware.chat.conversation_schemas import (
    ChatMessage,
    ToolCalls,
    ToolResponseMessage,
)
from aware.utils.logger.process_logger import ProcessLogger


class Conversation:
    """Conversation class to keep track of the messages and the current state of the conversation."""

    def __init__(self, process_id: str, process_logger: ProcessLogger):
        self.logger = process_logger.get_logger("conversation", should_print=True)
        self.logger.info(f"Starting new conversation for process_id: {process_id}")
        self.process_id = process_id

        self.model_name = Config().openai_model  # TODO: Enable more models.
        self.chat_database_handler = ChatDatabaseHandler(process_logger)
        self.messages = self.chat_database_handler.get_conversation(process_id)

    def delete_oldest_message(self) -> ChatMessage:
        removed_message = self.messages.pop(0)
        message_id = removed_message.message_id

        self.chat_database_handler.delete_message(self.process_id, message_id)
        return removed_message

    def get_current_tokens(self):
        """Get the current number of tokens in the conversation, excluding the system message."""

        return count_message_tokens(
            messages=self.to_string(),
            model_name=self.model_name,
        )

    def get_remaining_tokens(self):
        return Config().max_conversation_tokens - self.get_current_tokens()

    def reset(self):
        while self.messages:
            self.delete_oldest_message()

    def should_trigger_warning(self):
        warning_tokens = (
            Config().max_conversation_tokens * Config().conversation_warning_threshold
        )
        return self.get_current_tokens() >= int(warning_tokens)

    def to_string(self):
        conversation_string = "\n".join(
            [message.to_string() for message in self.messages]
        )
        return conversation_string

    def trim_conversation(self):
        current_message_tokens = self.get_current_tokens()
        while (current_message_tokens) > Config().max_conversation_tokens:
            # Check if the next message is a 'tool' message and the current one is 'assistant' with 'tool_calls'.
            if len(self.messages) > 2 and isinstance(self.messages[0] == ToolCalls):
                removed_message = (
                    self.delete_oldest_message()
                )  # Delete 'tool_calls' message.

                current_message_tokens -= count_message_tokens(
                    removed_message.to_string(), self.model_name
                )
                # Delete all the 'tool_response' messages.
                while len(self.messages) > 1 and isinstance(
                    self.messages[1], ToolResponseMessage
                ):
                    removed_tool_message = self.delete_oldest_message()
                    current_message_tokens -= count_message_tokens(
                        removed_tool_message.to_string(),
                        self.model_name,
                    )
            else:
                # Delete the oldest message if the above condition is not met.
                removed_message = self.delete_oldest_message()

                current_message_tokens -= count_message_tokens(
                    removed_message.to_string(), self.model_name
                )
