import json
from dataclasses import dataclass
from enum import Enum


class ProcessFlowType(Enum):
    INDEPENDENT = "independent"
    INTERACTIVE = "interactive"


class ProcessType(Enum):
    MAIN = "main"
    INTERNAL = "internal"


@dataclass
class ProcessData:
    id: str
    name: str
    capability_class: str
    prompt_name: str
    flow_type: ProcessFlowType
    type: ProcessType

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "capability_class": self.capability_class,
            "prompt_name": self.prompt_name,
            "flow_type": self.flow_type.value,
            "type": self.type.value,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str: str):
        data = json.loads(json_str)
        data["flow_type"] = ProcessFlowType(data["flow_type"])
        data["type"] = ProcessType(data["type"])
        return ProcessData(**data)
