from dataclasses import dataclass
import json
from typing import List

from aware.communications.topics.topic import Topic


@dataclass
class TopicPublisher:
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

    # TODO: implement me:
    def get_topics(self) -> List[Topic]:
        pass
