from dataclasses import dataclass
import json


@dataclass
class Subscription:
    def __init__(
        self,
        id: str,
        topic_name: str,
        content: str,
        description: str,
        timestamp: str,
    ):
        self.id = id
        self.topic_name = topic_name
        self.content = content
        self.description = description
        self.timestamp = timestamp

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)

    def to_string(self):
        return f"Topic: {self.topic_name}: {self.description}\nContent: {self.content}"
