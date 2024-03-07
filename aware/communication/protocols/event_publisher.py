import json
from typing import Any, Dict

from aware.communication.primitives.event import Event
from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)
from aware.communication.protocols.interface.protocol import Protocol


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
        PrimitivesDatabaseHandler().create_event(
            publisher_id=self.id, event_message=event_message
        )
