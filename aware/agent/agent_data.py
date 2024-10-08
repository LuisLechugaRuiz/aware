import json
from dataclasses import dataclass
from enum import Enum
from typing import List

# from aware.tools.profile import Profile


class AgentState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING_FOR_RESPONSE = "waiting_for_response"
    FINISHED = "finished"


class AgentMemoryMode(Enum):
    STATEFUL = "stateful"
    STATELESS = "stateless"


class ThoughtGeneratorMode(Enum):
    DISABLED = "disabled"
    PRE = "pre"
    PARALLEL = "parallel"
    POST = "post"


# TODO: Split between AgentConfig and InternalAgentData. TBD.
@dataclass
class AgentData:
    id: str
    name: str
    description: str
    context: str
    capability_class: str
    # task: str
    # instructions: str
    state: AgentState
    memory_mode: AgentMemoryMode
    modalities: List[str]
    thought_generator_mode: ThoughtGeneratorMode
    # profile: Profile

    def to_json(self):
        return json.dumps(self.to_dict(), default=lambda o: o.__dict__)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "context": self.context,
            "capability_class": self.capability_class,
            # "task": self.task,
            # "instructions": self.instructions,
            "state": self.state.value,
            "memory_mode": self.memory_mode.value,
            "modalities": self.modalities,
            "thought_generator_mode": self.thought_generator_mode.value,
            # "profile": json.loads(self.profile.to_json()),
        }

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        # data["profile"] = (
        #     Profile(profile=json.loads(data["profile"]))
        #     if isinstance(data["profile"], str)
        #     else Profile(profile=data["profile"])
        # )
        data["state"] = AgentState(data["state"])
        data["thought_generator_mode"] = ThoughtGeneratorMode(
            data["thought_generator_mode"]
        )
        return cls(**data)

    def to_prompt_kwargs(self):
        return {
            "agent_name": self.name,
            "context": self.context,
        }

    @classmethod
    def create_description(cls, name: str, description: str):
        return f"- Name: {name}\nDescription: {description}"
