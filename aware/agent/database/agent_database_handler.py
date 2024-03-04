from typing import Any, Dict, List

from aware.agent.agent_data import AgentData
from aware.agent.database.agent_redis_handler import (
    AgentRedisHandler,
)
from aware.agent.database.agent_supabase_handler import (
    AgentSupabaseHandler,
)
from aware.agent.agent_profile import AgentProfile
from aware.database.client_handlers import ClientHandlers
from aware.utils.logger.file_logger import FileLogger  # TODO: use agent logger?


class AgentDatabaseHandler:
    def __init__(self):
        self.redis_handler = AgentRedisHandler(
            client=ClientHandlers().get_redis_client()
        )
        self.supabase_handler = AgentSupabaseHandler(
            client=ClientHandlers().get_supabase_client()
        )
        self.logger = FileLogger("client_agent_handler")

    def add_active_agent(self, agent_id: str):
        self.redis_handler.add_active_agent(agent_id)
        self.supabase_handler.set_active_agent(agent_id, active=True)

    def create_agent(
        self,
        user_id: str,
        name: str,
        tools_class: str,
        memory_mode: str,
        modalities: List[str],
        thought_generator_mode: str,
    ) -> AgentData:
        self.logger.info("Creating agent")
        agent_data = self.supabase_handler.create_agent(
            user_id=user_id,
            name=name,
            tools_class=tools_class,
            memory_mode=memory_mode,
            modalities=modalities,
            thought_generator_mode=thought_generator_mode,
        )
        self.logger.info(f"Agent: {agent_data.id}, created on supabase")
        self.redis_handler.set_agent_data(agent_data)
        self.logger.info(f"Agent: {agent_data.id}, created on redis")
        return agent_data

    def create_profile(self, agent_id: str, profile: Dict[str, Any]):
        # TODO: address me.
        AgentProfile(profile=profile)

    def get_agent_data(self, agent_id: str) -> AgentData:
        agent_data = self.redis_handler.get_agent_data(agent_id)

        if agent_data is None:
            self.logger.info("Agent data not found in Redis")
            # Fetch agent data from Supabase
            agent_data = self.supabase_handler.get_agent_data(agent_id)
            if agent_data is None:
                raise Exception("Agent data not found")

            self.redis_handler.set_agent_data(agent_data)
        else:
            self.logger.info("Agent data found in Redis")

        return agent_data

    def get_agent_process_id(self, agent_id: str, process_name: str) -> str:
        process_id = self.redis_handler.get_agent_process_id(agent_id, process_name)

        if process_id is None:
            self.logger.info("Agent process id not found in Redis")
            # Fetch agent process id from Supabase
            process_id = self.supabase_handler.get_agent_process_id(
                agent_id, process_name
            )
            if process_id is None:
                raise Exception("Agent process id not found")

            self.redis_handler.set_agent_process_id(agent_id, process_name, process_id)
        else:
            self.logger.info("Agent process id found in Redis")

        return process_id

    def is_agent_active(self, agent_id: str) -> bool:
        return self.redis_handler.is_agent_active(agent_id)

    def remove_active_agent(self, agent_id: str):
        self.redis_handler.remove_active_agent(agent_id=agent_id)
        self.supabase_handler.set_active_agent(agent_id=agent_id, active=False)

    def update_agent_data(self, agent_data: AgentData):
        try:
            self.supabase_handler.update_agent_data(agent_data)
            self.redis_handler.set_agent_data(agent_data)
            return "Success"
        except Exception as e:
            return f"Failure: {str(e)}"
