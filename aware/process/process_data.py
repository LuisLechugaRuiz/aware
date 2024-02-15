import json
from dataclasses import dataclass
from enum import Enum


class ProcessFlowType(Enum):
    INDEPENDENT = "independent"
    INTERACTIVE = "interactive"


@dataclass
class ProcessData:
    id: str
    name: str
    tools_class: str
    task: str
    instructions: str
    flow_type: ProcessFlowType

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "tools_class": self.tools_class,
            "task": self.task,
            "instructions": self.instructions,
            "flow_type": self.flow_type.value,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str: str):
        data = json.loads(json_str)
        data["flow_type"] = ProcessFlowType(data["flow_type"])
        return ProcessData(**data)

    def to_prompt_kwargs(self):
        return {
            "task": self.task,
            "instructions": self.instructions,
        }
