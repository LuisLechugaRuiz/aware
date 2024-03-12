from dataclasses import dataclass
import json
from typing import Dict


@dataclass
class ProcessState:
    id: str
    name: str
    tools: Dict[str, str]
    task: str
    instructions: str

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)

    def to_prompt_kwargs(self):
        return {
            "task": self.task,
            "instructions": self.instructions,
        }
