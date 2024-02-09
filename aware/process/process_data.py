import json
from dataclasses import dataclass


@dataclass
class ProcessData:
    id: str
    name: str
    tools_class: str
    identity: str
    task: str
    instructions: str

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(
            self.to_dict(),
            default=lambda o: o.__dict__ if hasattr(o, "__dict__") else str(o),
        )

    @staticmethod
    def from_json(json_str: str):
        data = json.loads(json_str)
        return ProcessData(**data)

    def to_prompt_kwargs(self):
        return {
            "identity": self.identity,
            "task": self.task,
            "instructions": self.instructions,
        }
