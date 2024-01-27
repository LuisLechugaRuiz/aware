import json
from dataclasses import dataclass


@dataclass
class PromptData:
    module_name: str
    prompt_name: str

    def to_dict(self):
        return {
            "module_name": self.module_name,
            "prompt_name": self.prompt_name,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str: str):
        data = json.loads(json_str)
        return PromptData(**data)
