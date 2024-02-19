from dataclasses import dataclass
import json
from typing import List

from aware.agent.agent_data import AgentMemoryMode, ThoughtGeneratorMode


@dataclass
class AgentConfig:
    thought_generator_mode: ThoughtGeneratorMode
    memory_mode: AgentMemoryMode
    modalities: List[str]

    def to_dict(self):
        return {
            "thought_generator_mode": self.thought_generator_mode.value,
            "memory_mode": self.memory_mode.value,
            "modalities": self.modalities,
        }

    def from_json(cls, json_str):
        data = json.loads(json_str)
        data["thought_generator_mode"] = ThoughtGeneratorMode(
            data["thought_generator_mode"]
        )
        data["memory_mode"] = AgentMemoryMode(data["memory_mode"])
        return cls(**data)

    def to_json(self):
        return json.dumps(self.to_dict())
