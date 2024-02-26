from dataclasses import dataclass
import json


@dataclass
class EventPublisher:
    id: str
    user_id: str
    process_id: str
    event_type_id: str
    event_name: str

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)
