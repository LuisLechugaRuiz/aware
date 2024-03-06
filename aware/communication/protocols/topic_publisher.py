from dataclasses import dataclass
import json
from typing import Any, Dict, List

from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)
from aware.communication.primitives.interface.function_detail import FunctionDetail
from aware.communication.protocols.interface.protocol import Protocol


@dataclass
class TopicPublisher(Protocol):
    id: str
    user_id: str
    process_id: str
    topic_id: str
    topic_name: str
    topic_description: str
    message_format: Dict[str, str]

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)

    def update_topic(self, message: Dict[str, Any]):
        PrimitivesDatabaseHandler().update_topic(self.topic_id, message)

    def setup_functions(self) -> List[FunctionDetail]:
        return [
            FunctionDetail(
                name=self.topic_name,
                args=self.message_format,
                description=f"Call this function to publish on topic: {self.topic_name} with description: {self.topic_description}",
                callback=self.update_topic,
            )
        ]
