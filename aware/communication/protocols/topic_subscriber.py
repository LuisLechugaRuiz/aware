from dataclasses import dataclass
import json
from typing import Dict

from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)


@dataclass
class TopicSubscriber:
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

    def get_topic_update(self) -> str:
        topic = PrimitivesDatabaseHandler().get_topic(self.topic_id)
        return topic.to_string()
