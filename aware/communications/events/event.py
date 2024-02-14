from enum import Enum
import json


class EventStatus(Enum):
    PENDING = "pending"
    NOTIFIED = "notified"


class Event:
    def __init__(
        self,
        id: str,
        user_id: str,
        name: str,
        message_name: str,
        content: str,
        status: EventStatus,
        timestamp: str,
    ):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.message_name = message_name
        self.content = content
        self.status = status
        self.timestamp = timestamp

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "message_name": self.message_name,
            "content": self.content,
            "status": self.status.value,
            "timestamp": self.timestamp,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        data["status"] = EventStatus(data["status"])
        return cls(**data)
