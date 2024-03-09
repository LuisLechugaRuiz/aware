import json
from typing import Any, Dict, List

from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)
from aware.communication.primitives.interface.function_detail import FunctionDetail
from aware.communication.protocols.interface.protocol import Protocol


class TopicPublisher(Protocol):
    def __init__(
        self,
        id: str,
        user_id: str,
        process_id: str,
        topic_id: str,
        topic_name: str,
        topic_description: str,
        message_format: Dict[str, str],
    ):
        self.user_id = user_id
        self.process_id = process_id
        self.topic_id = topic_id
        self.topic_name = topic_name
        self.topic_description = topic_description
        self.message_format = message_format
        super().__init__(id=id)

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)

    def update_topic(self, message: Dict[str, Any]) -> str:
        PrimitivesDatabaseHandler().update_topic(self.topic_id, message)
        return "Topic updated successfully"

    @property
    def tools(self) -> List[FunctionDetail]:
        return [
            FunctionDetail(
                name=self.topic_name,
                args=self.message_format,
                description=f"Call this function to publish on topic: {self.topic_name} with description: {self.topic_description}",
                callback=self.update_topic,
                should_continue=True,
            )
        ]
