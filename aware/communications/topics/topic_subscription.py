from dataclasses import dataclass
import json


@dataclass
class TopicSubscription:
    def __init__(
        self,
        user_id: str,
        process_id: str,
        topic_id: str,
        topic_name: str,
    ):
        self.user_id = user_id
        self.process_id = process_id
        self.topic_id = topic_id
        self.topic_name = topic_name

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)
