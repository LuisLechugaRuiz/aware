import json
from typing import Dict


class WorkingMemory:
    def __init__(
        self,
        user_id: str,
        chat_id: str,
        user_name: str,
        thought: str,
        context: str,
        updated_at: str,
    ):
        self.user_name = user_name
        self.user_id = user_id
        self.chat_id = chat_id
        self.thought = thought
        self.context = context
        self.updated_at = updated_at

    def to_dict(self):
        return self.__dict__.copy()

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, data: Dict):
        data = json.loads(data)
        return cls(
            user_id=data["user_id"],
            user_name=data["user_name"],
            chat_id=data["chat_id"],
            thought=data["thought"],
            context=data["context"],
            updated_at=data["updated_at"],
        )
