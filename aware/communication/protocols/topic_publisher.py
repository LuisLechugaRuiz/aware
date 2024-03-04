from dataclasses import dataclass
import json
from typing import Dict, List, Optional

from aware.chat.parser.json_pydantic_parser import JsonPydanticParser
from aware.communication.primitives.topic import Topic


@dataclass
class TopicPublisher:
    id: str
    user_id: str
    process_id: str
    topic_id: str
    topic_name: str
    topic_description: str
    message_format: Dict[str, str]
    topic: Optional[Topic] = None

    def add_topic(self, topic: Topic):
        self.topic = topic

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)

    def get_topic_as_function(self) -> List[Topic]:
        topic_description = f"Call this function to publish on topic: {self.topic_name} with description: {self.topic_description}"
        return JsonPydanticParser.get_function_schema(
            name=self.topic_name,
            args=self.message_format,
            description=topic_description,
        )