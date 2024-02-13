import json


class Event:
    def __init__(self, id: str, name: str, content: str, timestamp: str):
        self.id = id
        self.name = name
        self.content = content
        self.timestamp = timestamp

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "content": self.content,
            "timestamp": self.timestamp,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)
