import json
from typing import Dict


class UserData:
    def __init__(
        self,
        user_id: str,
        user_name: str,
        api_key: str,
        assistant_agent_id: str,
        orchestrator_agent_id: str,
    ):
        self.user_id = user_id
        self.user_name = user_name
        self.api_key = api_key
        self.assistant_agent_id = assistant_agent_id
        self.orchestrator_agent_id = orchestrator_agent_id

    def to_dict(self):
        return self.__dict__.copy()

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, data: Dict):
        data = json.loads(data)
        return cls(
            user_id=data["user_id"],
            user_name=data["user_name"],
            api_key=data["api_key"],
            assistant_agent_id=data["assistant_agent_id"],
            orchestrator_agent_id=data["orchestrator_agent_id"],
        )
