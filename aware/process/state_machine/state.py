from dataclasses import dataclass
import json
from typing import Dict


@dataclass
class ProcessState:
    name: str
    tools: Dict[str, str]
    task: str
    instructions: str

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict())

    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)
