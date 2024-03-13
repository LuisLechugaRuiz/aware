from dataclasses import dataclass
import json
from typing import Dict

from aware.process.state_machine.transition import Transition


@dataclass
class ProcessState:
    name: str
    tool_transitions: Dict[str, Transition]
    task: str
    instructions: str

    def to_dict(self):
        return {
            "name": self.name,
            "tool_transitions": {tool: transition.to_dict() for tool, transition in self.tool_transitions.items()},
            "task": self.task,
            "instructions": self.instructions,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        data["tool_transitions"] = {tool: Transition(**transition) for tool, transition in data["tool_transitions"].items()}
        return cls(**data)

    def to_prompt_kwargs(self):
        return {
            "task": self.task,
            "instructions": self.instructions,
        }

    def tools_to_string(self):
        return "\n".join([f" - Tool: {tool} - Transition: {transition.to_string()}" for tool, transition in self.tool_transitions.items()])

    def to_string(self):
        return f"State: {self.name}\nTools:\n{self.tools_to_string()}\nTask: {self.task}\nInstructions: {self.instructions}"
