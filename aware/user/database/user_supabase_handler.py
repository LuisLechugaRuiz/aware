from supabase import Client

from aware.config.config import Config
from aware.utils.logger.user_logger import UserLogger


class UserSupabaseHandler:
    def __init__(self, client: Client, usre_logger: UserLogger):
        self.client = client
        self.logger = usre_logger.get_logger("user_messages")

    def acknowledge_user_message(
        self,
        message_id: str,
    ) -> None:
        self.client.table("user_messages").update(
            {"acknowledge": True}
        ).eq("message_id", message_id).execute()
