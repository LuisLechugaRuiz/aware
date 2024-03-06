from dataclasses import dataclass
import json
from typing import Any, Dict


@dataclass
class Topic:
    id: str
    user_id: str
    name: str
    description: str
    message: Dict[str, Any]
    message_format: Dict[str, Any]
    timestamp: str

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)

    def to_string(self):
        message_str = "\n".join(
            [f"{key}: {value}" for key, value in self.message.items()]
        )
        return f"{self.description}\n{message_str}"
