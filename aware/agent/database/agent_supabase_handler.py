from supabase import Client
from typing import Any, Dict, List, Optional

from aware.agent.agent_data import (
    AgentData,
    AgentMemoryMode,
    AgentState,
    ThoughtGeneratorMode,
)
from aware.agent.agent_profile import AgentProfile
from aware.utils.logger.user_logger import UserLogger


class AgentSupabaseHandler:
    def __init__(self, client: Client):
        self.client = client
        self.logger = UserLogger("supabase_agent_handler")

    def create_agent(
        self,
        user_id: str,
        name: str,
        capability_class: str,
        memory_mode: str,
        modalities: List[str],
        thought_generator_mode: str,
    ) -> AgentData:
        data = (
            self.client.table("agents")
            .insert(
                {
                    "user_id": user_id,
                    "name": name,
                    "capability_class": capability_class,
                    "memory_mode": memory_mode,
                    "modalities": modalities,
                    "thought_generator_mode": thought_generator_mode,
                }
            )
            .execute()
            .data
        )
        data = data[0]
        return AgentData(
            id=data["id"],
            name=data["name"],
            context=data["context"],
            capability_class=data["capability_class"],
            state=AgentState(data["state"]),
            memory_mode=AgentMemoryMode(data["memory_mode"]),
            modalities=data["modalities"],
            thought_generator_mode=ThoughtGeneratorMode(data["thought_generator_mode"]),
        )

    def create_profile(self, agent_id: str, profile: Dict[str, Any]):
        # TODO: address me.
        AgentProfile(profile=profile)

    def get_agent_data(self, agent_id: str):
        data = self.client.table("agents").select("*").eq("id", agent_id).execute().data
        if not data:
            return None
        data = data[0]
        return AgentData(
            id=agent_id,
            name=data["name"],
            task=data["task"],
            context=data["context"],
            state=AgentState(data["state"]),
            thought_generator_mode=ThoughtGeneratorMode(data["thought_generator_mode"]),
        )

    def get_agent_profile(self, agent_id: str) -> Optional[AgentProfile]:
        data = self.client.table("agents").select("*").eq("id", agent_id).execute().data
        if not data:
            return None
        return AgentProfile(profile=data[0]["profile"])

    def get_agent_process_id(self, agent_id: str, process_name: str) -> Optional[str]:
        data = (
            self.client.table("processes")
            .select("*")
            .eq("agent_id", agent_id)
            .eq("name", process_name)
            .execute()
            .data
        )
        if not data:
            return None
        return data[0]["id"]

    def set_active_agent(self, agent_id: str, active: bool):
        self.client.table("agents").update({"is_active": active}).eq(
            "id", agent_id
        ).execute()

    def update_agent_data(self, agent_data: AgentData):
        self.client.table("agents").update(agent_data.to_dict()).eq(
            "id", agent_data.id
        ).execute()

    def update_agent_profile(self, agent_id: str, profile: Dict[str, Any]):
        self.client.table("agents").update({"profile": profile}).eq(
            "id", agent_id
        ).execute()
