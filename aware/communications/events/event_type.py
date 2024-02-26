import json
from typing import Any, Dict


class EventType:
    def __init__(
        self,
        id: str,
        user_id: str,
        name: str,
        description: str,
        message_format: Dict[str, Any],
    ):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.description = description
        self.message_format = message_format

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "message_format": self.message_format,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)
