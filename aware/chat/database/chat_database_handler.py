from typing import List, Tuple

from aware.chat.call_info import CallInfo
from aware.chat.conversation_schemas import ChatMessage, JSONMessage
from aware.chat.database.chat_redis_handler import (
    ChatRedisHandler,
)
from aware.chat.database.chat_async_redis_handler import ChatAsyncRedisHandler
from aware.chat.database.chat_supabase_handler import (
    ChatSupabaseHandler,
)
from aware.process.process_ids import ProcessIds
from aware.database.client_handlers import ClientHandlers

# TODO: is this the right place to save UserData?
from aware.user.user_data import UserData
from aware.utils.logger.process_logger import ProcessLogger  # TODO: use agent logger?


class ChatDatabaseHandler:
    def __init__(self, process_logger: ProcessLogger):
        self.redis_handler = ChatRedisHandler(
            client=ClientHandlers().get_redis_client()
        )
        self.supabase_handler = ChatSupabaseHandler(
            client=ClientHandlers().get_supabase_client(), process_logger=process_logger
        )
        self.logger = process_logger.get_logger("chat_database_handler")

    def add_call_info(self, call_info: CallInfo):
        self.redis_handler.add_call_info(call_info)

    def add_message(
        self,
        process_ids: ProcessIds,
        json_message: JSONMessage,
    ) -> ChatMessage:
        self.logger.info("Adding to supa")
        chat_message = self.supabase_handler.add_message(
            process_id=process_ids.process_id,
            user_id=process_ids.user_id,
            json_message=json_message,
        )
        self.logger.info("Adding to redis")
        self.redis_handler.add_message(
            process_id=process_ids.process_id, chat_message=chat_message
        )
        return chat_message

    def clear_conversation_buffer(self, process_id: str):
        self.supabase_handler.clear_conversation_buffer(process_id)
        self.redis_handler.clear_conversation_buffer(process_id)

    def delete_message(self, process_id: str, message_id: str):
        self.supabase_handler.delete_message(message_id)
        self.redis_handler.delete_message(process_id, message_id)

    @staticmethod
    def get_async_redis_handler() -> ChatAsyncRedisHandler:
        return ChatAsyncRedisHandler(client=ClientHandlers().get_async_redis_client())

    # TODO: Clarify: Redis returns JsonMessage but Supabase ChatMessage...
    def get_conversation(self, process_id: str) -> List[ChatMessage]:
        conversation_messages = self.redis_handler.get_conversation(process_id)
        for index, message in enumerate(conversation_messages):
            self.logger.info(f"REDIS MESSAGE {index}: {message.to_string()}")
        if not conversation_messages:
            conversation_messages = self.supabase_handler.get_conversation(process_id)
            for message in conversation_messages:
                self.redis_handler.add_message(
                    process_id=process_id, chat_message=message
                )
        return conversation_messages

    # TODO: Clarify: Redis returns JsonMessage but Supabase ChatMessage...
    def get_conversation_buffer(self, process_id: str) -> List[ChatMessage]:
        conversation_messages = self.redis_handler.get_conversation_buffer(process_id)
        for index, message in enumerate(conversation_messages):
            self.logger.info(f"BUFFERED REDIS MESSAGE {index}: {message.to_string()}")
        if not conversation_messages:
            # If there are no buffered messages, get the buffered messages from supabase.
            conversation_messages = self.supabase_handler.get_conversation_buffer(
                process_id
            )
            for message in conversation_messages:
                self.redis_handler.add_message_to_buffer(
                    process_id=process_id, chat_message=message
                )
        return conversation_messages

    def get_conversation_with_keys(
        self, process_id: str
    ) -> List[Tuple[str, JSONMessage]]:
        return self.redis_handler.get_conversation_with_keys(process_id)

    def send_message_to_user(
        self,
        user_id: str,
        process_id: str,
        message_type: str,
        role: str,
        name: str,
        content: str,
    ):
        self.supabase_handler.send_message_to_user(
            user_id=user_id,
            process_id=process_id,
            message_type=message_type,
            role=role,
            name=name,
            content=content,
        )

    def set_user_data(self, user_data: UserData):
        self.redis_handler.set_user_data(user_data)

    def update_message(self, message_key: str, message: JSONMessage):
        # self.supabase_handler.update_message(process_id, message_id, message) # TODO: Implement me! refactor this function properly..
        self.redis_handler.update_message(message_key, message)
