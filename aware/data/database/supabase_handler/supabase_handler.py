from supabase import Client
from typing import List

from aware.chat.conversation_schemas import ChatMessage, JSONMessage
from aware.data.database.data import get_topics
from aware.config.config import Config
from aware.data.database.supabase_handler.messages_factory import MessagesFactory
from aware.utils.logger.file_logger import FileLogger


class SupabaseHandler:
    def __init__(self, client: Client):
        self.client = client

    def add_message(
        self, chat_id: str, user_id: str, process_name: str, json_message: JSONMessage
    ) -> ChatMessage:
        logger = FileLogger("migration_tests")
        invoke_options = {
            "p_chat_id": chat_id,
            "p_user_id": user_id,
            "p_model": Config().aware_model,
            "p_process_name": process_name,
            "p_message_type": json_message.__class__.__name__,
        }
        # Add p_ to all the keys in json_message
        json_message_dict = json_message.to_openai_dict()
        json_message_dict = {
            "p_" + key: value for key, value in json_message_dict.items()
        }
        # Expand dictionary with json_message data
        invoke_options.update(json_message_dict)
        logger.info("DEBUG - PRE CALL")
        response = self.client.rpc("insert_new_message", invoke_options).execute().data
        logger.info(f"DEBUG - POST CALL: {response}")
        response = response[0]
        logger.info("DEBUG - AFTER RESPONSE")
        return ChatMessage(
            message_id=response["id"],
            timestamp=response["created_at"],
            message=json_message,
        )

    def create_topics(self, user_id: str):
        logger = FileLogger("migration_tests")
        topics_data = get_topics()
        if topics_data is None:
            logger.error("DEBUG - No topics data")
            raise Exception("No topics data")
        logger.info(f"DEBUG - Got topics data: {topics_data}")
        for topic_name, topic_description in topics_data.items():
            self.create_topic(user_id, topic_name, topic_description)
            logger.info(f"DEBUG - Created topic {topic_name}")

    def create_topic(self, user_id: str, topic_name: str, topic_description: str):
        logger = FileLogger("migration_tests")
        existing_topic = (
            self.client.table("topics")
            .select("*")
            .eq("user_id", user_id)
            .eq("name", topic_name)
            .execute()
        ).data
        logger.info(f"DEBUG - Got existing topic: {existing_topic}")
        if not existing_topic:
            logger.info(f"DEBUG - Creating topic {topic_name}")
            self.client.table("topics").insert(
                {
                    "user_id": user_id,
                    "name": topic_name,
                    "content": "",
                    "description": topic_description,
                }
            ).execute()

    def delete_message(self, message_id):
        invoke_options = {"p_message_id": message_id}
        response = self.client.rpc("soft_delete_message", invoke_options).execute().data
        return response

    def get_user_profile(self, user_id: str):
        data = (
            self.client.table("user_profiles")
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

    def get_topic_content(self, user_id: str, name: str):
        data = (
            self.client.table("topics")
            .select("*")
            .eq("user_id", user_id)
            .eq("name", name)
            .execute()
            .data
        )
        if not data:
            return None
        data = data[0]
        return data["content"]

    def get_ui_profile(self, user_id: str):
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

    def set_topic_content(self, user_id: str, name: str, content: str):
        data = (
            self.client.table("topics")
            .select("*")
            .eq("user_id", user_id)
            .eq("name", name)
            .execute()
            .data
        )
        if not data:
            raise Exception("Topic not found")
        else:
            self.client.table("topics").update({"content": content}).eq(
                "user_id", user_id
            ).eq("name", name).execute()

    def send_message_to_user(
        self,
        chat_id: str,
        user_id: str,
        process_name: str,
        message_type: str,
        role: str,
        name: str,
        content: str,
    ):
        logger = FileLogger("migration_tests")
        logger.info(f"DEBUG - Sending message to user {user_id}")
        invoke_options = {
            "p_chat_id": chat_id,
            "p_user_id": user_id,
            "p_model": Config().aware_model,
            "p_process_name": process_name,
            "p_message_type": message_type,
            "p_role": role,
            "p_name": name,
            "p_content": content,
        }
        response = (
            self.client.rpc("send_message_to_user", invoke_options).execute().data
        )
        logger.info(f"DEBUG - Response: {response}")
        return response

    def remove_frontend_message(self, message_id: str):
        self.client.table("frontend_messages").delete().eq("id", message_id).execute()

    def remove_new_user_notification(self, notification_id: str):
        self.client.table("new_user_notification").delete().eq(
            "id", notification_id
        ).execute()

    def update_user_profile(self, user_id: str, profile: dict):
        self.client.table("profiles").update(profile).eq("user_id", user_id).execute()
