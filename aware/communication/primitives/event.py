from enum import Enum
import json
from typing import Any, Dict

from aware.communication.primitives.interface.input import Input
from aware.chat.conversation_schemas import UserMessage


class EventStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"


# TODO: Split between EventTypeConfig and EventConfig...
@dataclass
class EventConfig:
    name: str
    description: str
    message_format: Dict[str, Any]

    def to_json(self):
        return json.dumps(self.__dict__)

    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)


class EventType:
    def __init__(
        self,
        id: str,
        user_id: str,
        name: str,
        description: str,
        message_format: Dict[str, Any],
        priority: int
    ):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.description = description
        self.message_format = message_format
        self.priority = priority

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "message_format": self.message_format,
            "priority": self.priority
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)


class Event(Input):
    def __init__(
        self,
        id: str,
        user_id: str,
        event_type_id: str,
        event_name: str,
        event_description: str,
        event_message: Dict[str, Any],
        event_message_format: Dict[str, Any],
        event_details: str,
        priority: int,
        status: EventStatus,
        timestamp: str,
    ):
        self.user_id = user_id
        self.event_type_id = event_type_id
        self.event_name = event_name
        self.event_description = event_description
        self.event_message = event_message
        self.event_message_format = event_message_format
        self.event_details = event_details
        self.status = status
        self.timestamp = timestamp
        super().__init__(id=id, priority=priority)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_type_id": self.event_type_id,
            "event_name": self.event_name,
            "event_description": self.event_description,
            "event_message": self.event_message,
            "event_message_format": self.event_message_format,
            "event_details": self.event_details,
            "priority": self.priority,
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

    def dict_to_string(self, dict: Dict[str, Any]):
        return "\n".join([f"{key}: {value}" for key, value in dict.items()])

    def input_to_prompt_string(self) -> str:
        return f"Event: {self.dict_to_string(self.event_message)}"

    def get_type(self) -> str:
        return "event"

    def input_to_user_message(self) -> UserMessage:
        return UserMessage(
            name=self.event_name,
            content=f"Received new event: {self.input_to_prompt_string()}",
        )
