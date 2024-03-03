from redis import Redis
from typing import Optional

from aware.agent.agent_data import AgentData


class AgentRedisHandler:
    def __init__(self, client: Redis):
        self.client = client

    def add_active_agent(self, agent_id: str):
        self.client.sadd("active_agents", agent_id)

    def get_agent_data(self, agent_id: str) -> Optional[AgentData]:
        data = self.client.get(f"agent:{agent_id}")
        if data:
            return AgentData.from_json(data)
        return None

    def get_agent_process_id(self, agent_id: str, process_name: str) -> Optional[str]:
        process_id = self.client.get(f"agent:{agent_id}:process_name:{process_name}")
        if process_id:
            return process_id.decode()
        return None

    def is_agent_active(self, agent_id: str) -> bool:
        return self.client.sismember("active_agents", agent_id)

    def set_agent_data(self, agent_data: AgentData):
        self.client.set(
            f"agent:{agent_data.id}",
            agent_data.to_json(),
        )

    def set_agent_process_id(self, agent_id: str, process_name: str, process_id: str):
        self.client.set(
            f"agent:{agent_id}:process_name:{process_name}",
            process_id,
        )
        self.client.set(
            f"process:{process_id}:agent_id",
            agent_id,
        )

    def remove_active_agent(self, agent_id: str):
        self.client.srem("active_agents", agent_id)
