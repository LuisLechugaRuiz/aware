from supabase import Client
from typing import List, Optional

from aware.agent.memory.new_working_memory import WorkingMemory
from aware.chat.new_conversation_schemas import ChatMessage, JSONMessage
from aware.config.config import Config
from aware.data.database.supabase_handler.messages_factory import MessagesFactory
from aware.utils.logger.file_logger import FileLogger


class SupabaseHandler:
    def __init__(self, client: Client):
        self.client = client

    def add_message(
        self, chat_id: str, user_id: str, json_message: JSONMessage
    ) -> ChatMessage:
        invoke_options = {
            "p_chat_id": chat_id,
            "p_user_id": user_id,
            "p_model": Config().openai_model,
            "p_message_type": json_message.__name__,
        }
        # Expand dictionary with json_message data
        invoke_options.update(json_message.to_dict())
        response = self.client.rpc("insert_new_message", invoke_options).execute().data
        data = response[0]
        return ChatMessage(
            message_id=data["id"],
            timestamp=data["created_at"],
            message=json_message,
        )

    def delete_message(self, message_id):
        invoke_options = {"p_message_id": message_id}
        response = self.client.rpc("soft_delete_message", invoke_options).execute().data
        return response

    def get_user_data(self, user_id: str):
        return self.client.table("users").select("*").eq("id", user_id).execute().data

    def get_user_profile(self, user_id: str):
        data = (
            self.client.table("profiles")
            .select("*")
            .eq("user_id", user_id)
            .execute()
            .data
        )
        if not data:
            return None
        return data[0]

    def get_active_messages(self, chat_id: str, process_name: str) -> List[ChatMessage]:
        log = FileLogger("migration_tests")
        invoke_options = {"p_chat_id": chat_id, "p_process_name": process_name}
        log.info("PRE INVOKE with id: " + chat_id)
        log.info("INFO: " + str({"body": invoke_options, "responseType": "json"}))
        ordered_messages = (
            self.client.rpc("get_active_messages", invoke_options).execute().data
        )
        log.info("POST INVOKE, response: " + str(ordered_messages))
        messages = []
        if ordered_messages:
            for row in ordered_messages:
                log.info(f"Row: {str(row)}")
                messages.append(MessagesFactory.create_message(row))
        return messages

    def get_working_memory(self, user_id: str) -> Optional[WorkingMemory]:
        data = (
            self.client.table("working_memory")
            .select("*")
            .eq("user_id", user_id)
            .execute()
            .data
        )
        if not data:
            return None
        data = data[0]
        return WorkingMemory(
            user_id=user_id,
            chat_id=data["chat_id"],
            user_name=data["user_name"],
            thought=data["thought"],
            context=data["context"],
            updated_at=data["updated_at"],
        )

    def set_working_memory(self, working_memory: WorkingMemory):
        user_id = working_memory.user_id
        existing_working_memory = (
            self.client.table("working_memory")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        working_memory_dict = working_memory.to_dict()
        if existing_working_memory:
            self.client.table("working_memory").insert(working_memory_dict).execute()
        else:
            self.client.table("working_memory").update(working_memory_dict).eq(
                "user_id", user_id
            ).execute()
