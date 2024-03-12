import json
from dataclasses import dataclass

from aware.process.process_data import ProcessFlowType, ProcessType


# TODO: Refactor, same than process data but without ID to get it from cfg.
@dataclass
class ProcessConfig:
    id: str
    name: str
    capability_class: str
    prompt_name: str
    flow_type: ProcessFlowType
    type: ProcessType

    def to_dict(self):
        return {
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
        return ProcessConfig(**data)
