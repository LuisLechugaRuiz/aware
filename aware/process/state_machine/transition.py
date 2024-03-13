from dataclasses import dataclass
from enum import Enum
import json
from typing import Optional


class TransitionType(Enum):
    END = "end"
    CONTINUE = "continue"
    OTHER = "other"


@dataclass
class Transition:
    type: TransitionType
    new_state: Optional[str] = None

    def to_string(self):
        if self.type == TransitionType.OTHER:
            transition = self.new_state
        else:
            transition = self.type.name
        return transition

    def to_dict(self):
        return {
            "type": self.type.value,
            "new_state": self.new_state,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        data["type"] = TransitionType(data["type"])
        return cls(**data)
