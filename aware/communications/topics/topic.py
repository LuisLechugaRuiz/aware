from dataclasses import dataclass
import json


@dataclass
class Topic:
    id: str
    user_id: str
    topic_name: str
    description: str
    content: str
    timestamp: str

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)

    def to_string(self):
        return f"{self.description}\n{self.content}"
