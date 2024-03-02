from dataclasses import dataclass
import json
from typing import Dict


# TODO: How to have access to current requests from subscriber?
# - We can't access here to ClientHandlers, so we have two options:
#   1. We can pass the request to the subscriber when it is created.
#       - Pros: We can access the request directy at subscriber.
#       - Cons: We need to pass the request to the subscriber everytime we access it.
#   2. We can use an external class to retrieve the request for the specific subscriber.
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
