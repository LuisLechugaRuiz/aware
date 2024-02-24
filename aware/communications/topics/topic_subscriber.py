from dataclasses import dataclass
import json


@dataclass
class TopicSubscriber:
    id: str
    user_id: str
    process_id: str
    topic_id: str
    topic_message_id: str
    topic_name: str

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)
