from dataclasses import dataclass
import json


# TODO: Override by capability.capability
@dataclass
class Capability:
    user_id: str
    process_ids: str
    name: str
    description: str

    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)

    def to_json(self):
        return json.dumps(self.__dict__)
