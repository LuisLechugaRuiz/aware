import json
from typing import Any, Dict, List
from openai.types.chat import ChatCompletionMessageToolCallParam

from aware.config.config import Config
from aware.data.data_saver import DataSaver
from aware.utils.helpers import count_message_tokens

from aware.chat.new_conversation_schemas import (
    JSONMessage,
    ToolCalls,
    ToolResponseMessage,
)
from aware.data.database.client_handlers import ClientHandlers


class Conversation:
    """Conversation class to keep track of the messages and the current state of the conversation."""

    def __init__(self, chat_id: str):
        self.model_name = Config().openai_model  # TODO: Enable more models.
        self.redis_handler = ClientHandlers().get_redis_handler()
        self.supabase_handler = ClientHandlers().get_supabase_handler()
        conversation_messages = self.redis_handler.get_conversation(chat_id)
        if not conversation_messages:
            # TODO: Get from Supabase and fill Redis.
            pass

        self.messages: List[JSONMessage] = conversation_messages

    def on_new_message(self, message: JSONMessage):
        current_message_tokens = self.get_current_tokens()
        new_message_tokens = count_message_tokens(message.to_string(), self.model_name)
        while (
            current_message_tokens + new_message_tokens
        ) > Config().max_conversation_tokens:
            # Check if the next message is a 'tool' message and the current one is 'assistant' with 'tool_calls'.
            if len(self.messages) > 2 and isinstance(self.messages[0] == ToolCalls):
                removed_message = self.messages.pop(0)  # Remove 'tool_calls' message.

                # TODO: REMOVE MESSAGE FROM REDIS AND SET IT AS NO ACTIVE AT SUPABASE.

                current_message_tokens -= count_message_tokens(
                    removed_message.to_string(), self.model_name
                )
                # Remove all the 'tool_response' messages.
                while len(self.messages) > 1 and isinstance(
                    self.messages[1], ToolResponseMessage
                ):
                    removed_tool_message = self.messages.pop(0)
                    current_message_tokens -= count_message_tokens(
                        removed_tool_message.to_string(),
                        self.model_name,
                    )
            else:
                # Remove the oldest message if the above condition is not met.
                removed_message = self.messages.pop(0)

                # TODO: REMOVE MESSAGE FROM REDIS AND SET IT AS NO ACTIVE AT SUPABASE.

                current_message_tokens -= count_message_tokens(
                    removed_message.to_string(), self.model_name
                )
        # TODO: ADD MESSAGE AT REDIS AND SUPABASE.
        self.messages.append(message)

        # self.data_saver.add_message(message)

    def get_current_tokens(self):
        """Get the current number of tokens in the conversation, excluding the system message."""

        return count_message_tokens(
            messages=self.to_string(get_system_message=False),
            model_name=self.model_name,
        )

    def to_string(self, get_system_message: bool = True):
        start_index = 0 if get_system_message else 1

        messages_to_convert = self.messages[start_index:]

        conversation_string = "\n".join(
            [message.to_string() for message in messages_to_convert]
        )
        return conversation_string

    def get_remaining_tokens(self):
        return Config().max_conversation_tokens - self.get_current_tokens()

    def should_trigger_warning(self):
        warning_tokens = (
            Config().max_conversation_tokens * Config().conversation_warning_threshold
        )
        return self.get_current_tokens() >= int(warning_tokens)
