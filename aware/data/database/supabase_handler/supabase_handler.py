from supabase import Client
from typing import Optional

from aware.agent.memory.new_working_memory import WorkingMemory


class SupabaseHandler:
    def __init__(self, client: Client):
        self.client = client

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

    def get_messages(self, chat_id: str):
        return (
            self.client.table("messages")
            .select("*")
            .eq("chat_id", chat_id)
            .execute()
            .data
        )

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
        working_memory_json = working_memory.to_json()
        if existing_working_memory:
            self.client.table("working_memory").insert(working_memory_json).execute()
        else:
            self.client.table("working_memory").update(working_memory_json).eq(
                "user_id", user_id
            ).execute()
