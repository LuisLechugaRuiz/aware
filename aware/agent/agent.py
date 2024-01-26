import json
from dataclasses import dataclass

from aware.tools.profile import Profile


@dataclass
class Agent:
    id: str
    name: str
    thought: str
    context: str
    profile: Profile
    main_process_id: str
    thought_generator_process_id: str
    context_manager_process_id: str
    data_storage_manager_process_id: str

    def to_json(self):
        return json.dumps(
            self.to_dict(),
            default=lambda o: o.__dict__ if hasattr(o, "__dict__") else str(o),
        )

    def to_dict(self):
        return {
            "name": self.name,
            "thought": self.thought,
            "context": self.context,
            "profile": json.loads(self.profile.to_json()),
            "main_process_id": self.main_process_id,
            "thought_generator_process_id": self.thought_generator_process_id,
            "context_manager_process_id": self.context_manager_process_id,
            "data_storage_manager_process_id": self.data_storage_manager_process_id,
        }

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        data["profile"] = (
            Profile(profile=json.loads(data["profile"]))
            if isinstance(data["profile"], str)
            else Profile(profile=data["profile"])
        )
        return cls(**data)
