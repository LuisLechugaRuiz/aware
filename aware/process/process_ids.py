import json
from dataclasses import dataclass


@dataclass
class ProcessIds:
    user_id: str
    agent_id: str
    process_id: str

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "process_id": self.process_id,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str: str):
        data = json.loads(json_str)
        return ProcessIds(**data)
