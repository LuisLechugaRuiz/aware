import json
from dataclasses import dataclass

# from aware.tools.profile import Profile


@dataclass
class AgentData:
    id: str
    name: str
    task: str
    instructions: str
    thought: str
    context: str
    # profile: Profile

    def to_json(self):
        return json.dumps(self.to_dict(), default=lambda o: o.__dict__)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "task": self.task,
            "instructions": self.instructions,
            "thought": self.thought,
            "context": self.context,
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
        return cls(**data)