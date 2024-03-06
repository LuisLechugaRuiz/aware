from dataclasses import dataclass
import json
from typing import Any, Dict

from aware.communication.primitives.event import Event
from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)


@dataclass
class EventPublisher:
    id: str
    user_id: str
    process_id: str
    event_type_id: str
    event_name: str
    event_description: str
    event_format: Dict[str, str]

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
