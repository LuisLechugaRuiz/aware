from dataclasses import dataclass
import json


@dataclass
class EventSubscription:
    def __init__(
        self,
        user_id: str,
        process_id: str,
        event_type_id: str,
        event_name: str,
    ):
        self.user_id = user_id
        self.process_id = process_id
        self.event_type_id = event_type_id
        self.event_name = event_name

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)
