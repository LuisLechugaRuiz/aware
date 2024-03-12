from dataclasses import dataclass
import json
from typing import Dict, List

from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)
from aware.communication.primitives.interface.function_detail import FunctionDetail
from aware.communication.protocols.interface.protocol import Protocol


@dataclass
class TopicSubscriberConfig:
    topic_name: str

    def to_json(self):
        return {
            "topic_name": self.topic_name,
        }

    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)


# TODO: Update to input_protocol.
class TopicSubscriber(Protocol):
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

    def get_topic_update(self) -> str:
        topic = PrimitivesDatabaseHandler().get_topic(self.topic_id)
        return topic.to_string()

    @property
    # TODO: add set_topic_processed ??
    def tools(self) -> List[FunctionDetail]:
        return []
