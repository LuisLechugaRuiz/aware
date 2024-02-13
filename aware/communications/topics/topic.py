from dataclasses import dataclass
import json


@dataclass
class Topic:
    def __init__(
        self,
        id: str,
        user_id: str,
        topic_name: str,
        description: str,
        content: str,
        timestamp: str,
    ):
        self.id = id
        self.user_id = user_id
        self.topic_name = topic_name
        self.description = description
        self.content = content
        self.timestamp = timestamp

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)
