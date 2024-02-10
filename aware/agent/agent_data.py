import json
from dataclasses import dataclass
from enum import Enum

# from aware.tools.profile import Profile


class ThoughtGeneratorMode(Enum):
    PRE = "pre"
    PARALLEL = "parallel"
    POST = "post"


class AgentState(Enum):
    IDLE = "idle"
    MAIN_PROCESS = "main_process"
    THOUGHT_GENERATOR = "thought_generator"


@dataclass
class AgentData:
    id: str
    name: str
    context: str
    tools_class: str
    identity: str
    task: str
    instructions: str
    state: AgentState
    thought_generator_mode: ThoughtGeneratorMode
    # profile: Profile

    def to_json(self):
        return json.dumps(self.to_dict(), default=lambda o: o.__dict__)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "context": self.context,
            "tools_class": self.tools_class,
            "identity": self.identity,
            "task": self.task,
            "instructions": self.instructions,
            "state": self.state.value,
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
            "agent": self.name,
            "agent_task": self.task,
            "context": self.context,
        }

    def to_description_string(self):
        return f"{self.name} {self.identity}\n{self.task}"

    @classmethod
    def create_description(cls, name: str, identity: str, task: str):
        return f"- Name: {name}\n- Identity: {identity}\nTask: {task}"
