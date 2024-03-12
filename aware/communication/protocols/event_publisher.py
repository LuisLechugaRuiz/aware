from dataclasses import dataclass
import json
from typing import Any, Dict, List

from aware.communication.primitives.event import Event
from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)
from aware.communication.primitives.interface.function_detail import FunctionDetail
from aware.communication.protocols.interface.protocol import Protocol


@dataclass
class EventPublisherConfig:
    event_name: str

    def to_json(self):
        return {
            "event_name": self.event_name
        }

    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)


class EventPublisher(Protocol):
    def __init__(
        self,
        id: str,
        user_id: str,
        process_id: str,
        event_type_id: str,
        event_name: str,
        event_description: str,
        event_format: Dict[str, str],
    ):
        self.user_id = user_id
        self.process_id = process_id
        self.event_type_id = event_type_id
        self.event_name = event_name
        self.event_description = event_description
        self.event_format = event_format
        super().__init__(id=id)

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)

    def create_event(self, event_message: Dict[str, Any]) -> Event:
        event = PrimitivesDatabaseHandler().create_event(
            publisher_id=self.id, event_message=event_message
        )
        if event.error:
            raise Exception(f"Error creating event: {event.error}")

        self.send_communication(task_name="create_event", primitive_str=event.data.to_json())
        return "Event created successfully."

    @property
    def tools(self) -> List[FunctionDetail]:
        return [
            FunctionDetail(
                name=self.event_name,
                args=self.event_format,
                description=f"Call this function to publish event: {self.event_name} with description: {self.event_description}",
                callback=self.create_event,
            )
        ]
