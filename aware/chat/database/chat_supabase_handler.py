from supabase import Client
from typing import List

from aware.chat.conversation_schemas import ChatMessage, JSONMessage
from aware.chat.database.messages_factory import MessagesFactory
from aware.config.config import Config
from aware.utils.logger.process_logger import ProcessLogger


class ChatSupabaseHandler:
    def __init__(self, client: Client, process_logger: ProcessLogger):
        self.client = client
        self.logger = process_logger.get_logger("chat_supabase_handler")

    def add_message(
        self,
        user_id: str,
        process_id: str,
        json_message: JSONMessage,
    ) -> ChatMessage:
        invoke_options = {
            "p_user_id": user_id,
            "p_process_id": process_id,
            "p_model": Config().aware_model,
            "p_message_type": json_message.__class__.__name__,
        }
        # Add p_ to all the keys in json_message
        json_message_dict = json_message.to_openai_dict()
        json_message_dict = {
            "p_" + key: value for key, value in json_message_dict.items()
        }
        # Expand dictionary with json_message data
        invoke_options.update(json_message_dict)
        self.logger.info("Adding message to database")
        response = self.client.rpc("insert_new_message", invoke_options).execute().data
        self.logger.info(f"Database acknowledge {response}")
        response = response[0]
        return ChatMessage(
            message_id=response["id"],
            timestamp=response["created_at"],
            message=json_message,
        )

    def clear_conversation_buffer(self, process_id: str):
        response = self.client.rpc(
            "clear_conversation_buffer", {"p_process_id": process_id}
        ).execute()
        return response

    def delete_message(self, message_id):
        response = (
            self.client.rpc("soft_delete_message", {"p_message_id": message_id})
            .execute()
            .data
        )
        return response

    def get_conversation(self, process_id: str) -> List[ChatMessage]:
        self.logger.info(f"Getting active messages for: {process_id}")
        ordered_messages = (
            self.client.rpc("get_active_messages", {"p_process_id": process_id})
            .execute()
            .data
        )
        self.logger.info(f"Active messages: {str(ordered_messages)}")
        messages = []
        if ordered_messages:
            for row in ordered_messages:
                messages.append(MessagesFactory.create_message(row))
        return messages

    def get_conversation_buffer(self, process_id: str) -> List[ChatMessage]:
        self.logger.info(f"Getting buffered messages for: {process_id}")
        ordered_messages = (
            self.client.rpc("get_buffered_messages", {"p_process_id": process_id})
            .execute()
            .data
        )
        self.logger.info(f"Buffered messages: {str(ordered_messages)}")
        messages = []
        if ordered_messages:
            for row in ordered_messages:
                messages.append(MessagesFactory.create_message(row))
        return messages

    def send_message_to_user(
        self,
        user_id: str,
        process_id: str,
        message_type: str,
        role: str,
        name: str,
        content: str,
    ):
        self.logger.info(f"Sending message: {content} to user {user_id}")
        invoke_options = {
            "p_user_id": user_id,
            "p_process_id": process_id,
            "p_model": Config().aware_model,
            "p_message_type": message_type,
            "p_role": role,
            "p_name": name,
            "p_content": content,
        }
        response = (
            self.client.rpc("send_message_to_user", invoke_options).execute().data
        )
        self.logger.info(f"Database acknowledge: {response}")
        return response
