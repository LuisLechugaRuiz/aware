from enum import Enum
import json
from typing import Any, Dict


class EventStatus(Enum):
    PENDING = "pending"
    NOTIFIED = "notified"


class Event:
    def __init__(
        self,
        id: str,
        user_id: str,
        event_type_id: str,
        event_name: str,
        event_description: str,
        event_message: Dict[str, Any],
        event_format: Dict[str, Any],
        status: EventStatus,
        timestamp: str,
    ):
        self.id = id
        self.user_id = user_id
        self.event_type_id = event_type_id
        self.event_name = event_name
        self.event_description = event_description
        self.event_message = event_message
        self.event_format = event_format
        self.status = status
        self.timestamp = timestamp

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_type_id": self.event_type_id,
            "event_name": self.event_name,
            "event_description": self.event_description,
            "event_message": self.event_message,
            "event_format": self.event_format,
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
