import json
from typing import List


class Event:
    def __init__(
        self,
        id: str,
        name: str,
        content: str,
        timestamp: str,
        subscribed_processes: List[str],
    ):
        self.id = id
        self.name = name
        self.content = content
        self.timestamp = timestamp
        self.subscribed_processes = subscribed_processes

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "content": self.content,
            "timestamp": self.timestamp,
            "subscribed_processes": self.subscribed_processes,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)
