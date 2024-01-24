from typing import List

from aware.config.config import Config
from aware.data.data_saver import DataSaver
from aware.utils.helpers import count_message_tokens

from aware.chat.conversation_schemas import (
    ChatMessage,
    ToolCalls,
    ToolResponseMessage,
)
from aware.data.database.client_handlers import ClientHandlers
from aware.utils.logger.file_logger import FileLogger


class Conversation:
    """Conversation class to keep track of the messages and the current state of the conversation."""

    def __init__(self, chat_id: str, user_id: str, process_name: str):
        log = FileLogger("migration_tests", should_print=True)
        log.info(
            f"Starting new conversation for chat_id: {chat_id} and user_id: {user_id}"
        )

        self.chat_id = chat_id
        self.user_id = user_id
        self.process_name = process_name

        self.model_name = Config().openai_model  # TODO: Enable more models.
        self.redis_handler = ClientHandlers().get_redis_handler()
        self.supabase_handler = ClientHandlers().get_supabase_handler()
        conversation_messages = self.redis_handler.get_conversation(
            chat_id, process_name
        )
        for index, message in enumerate(conversation_messages):
            log.info(f"REDIS MESSAGE {index}: {message.to_string()}")
        if not conversation_messages:
            conversation_messages = self.supabase_handler.get_active_messages(
                chat_id, process_name
            )
            for message in conversation_messages:
                self.redis_handler.add_message(chat_id, message)
        self.messages: List[ChatMessage] = conversation_messages

    def delete_oldest_message(self) -> ChatMessage:
        removed_message = self.messages.pop(0)
        message_id = removed_message.message_id

        self.supabase_handler.delete_message(message_id)
        self.redis_handler.delete_message(self.chat_id, message_id, self.process_name)

        return removed_message

    def get_current_tokens(self):
        """Get the current number of tokens in the conversation, excluding the system message."""

        return count_message_tokens(
            messages=self.to_string(get_system_message=False),
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

    def to_string(self, get_system_message: bool = True):
        start_index = 0 if get_system_message else 1

        messages_to_convert = self.messages[start_index:]

        conversation_string = "\n".join(
            [message.to_string() for message in messages_to_convert]
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
