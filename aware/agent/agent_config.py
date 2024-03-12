from dataclasses import dataclass
import json
from typing import List

from aware.agent.agent_data import AgentMemoryMode, ThoughtGeneratorMode


@dataclass
class AgentConfig:
    name: str
    description: str
    capability_class: str
    memory_mode: AgentMemoryMode
    modalities: List[str]
    thought_generator_mode: ThoughtGeneratorMode

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "capability_class": self.capability_class,
            "memory_mode": self.memory_mode.value,
            "modalities": self.modalities,
            "thought_generator_mode": self.thought_generator_mode.value,
        }
    
    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        data["memory_mode"] = AgentMemoryMode(data["memory_mode"])
        data["thought_generator_mode"] = ThoughtGeneratorMode(
            data["thought_generator_mode"]
        )
        return cls(**data)

    def to_json(self):
        return json.dumps(self.to_dict())
