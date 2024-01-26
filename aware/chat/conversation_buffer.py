from typing import List

from aware.config.config import Config
from aware.data.data_saver import DataSaver
from aware.utils.helpers import count_message_tokens

from aware.chat.conversation_schemas import (
    ChatMessage,
)
from aware.data.database.client_handlers import ClientHandlers
from aware.utils.logger.file_logger import FileLogger


class ConversationBuffer:
    """Conversation class to keep track of the messages and the current state of the conversation."""

    def __init__(self, process_id: str):
        log = FileLogger("migration_tests", should_print=True)
        log.info(f"Starting new conversation buffer for process_id: {process_id}")
        self.process_id = process_id

        self.model_name = Config().openai_model  # TODO: Enable more models.
        self.redis_handler = ClientHandlers().get_redis_handler()
        self.supabase_handler = ClientHandlers().get_supabase_handler()
        # Get the buffered messages from redis.
        conversation_messages = self.redis_handler.get_conversation_buffer(process_id)
        for index, message in enumerate(conversation_messages):
            log.info(f"REDIS MESSAGE {index}: {message.to_string()}")
        if not conversation_messages:
            # If there are no buffered messages, get the buffered messages from supabase.
            conversation_messages = self.supabase_handler.get_buffered_messages(
                process_id
            )
            for message in conversation_messages:
                self.redis_handler.add_message_to_buffer(
                    process_id=process_id, chat_message=message
                )
        self.messages: List[ChatMessage] = conversation_messages

    def get_current_tokens(self):
        """Get the current number of tokens in the conversation, excluding the system message."""

        return count_message_tokens(
            messages=self.to_string(),
            model_name=self.model_name,
        )

    def get_remaining_tokens(self):
        return Config().max_conversation_tokens - self.get_current_tokens()

    def reset(self):
        self.redis_handler.clear_conversation_buffer()

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
