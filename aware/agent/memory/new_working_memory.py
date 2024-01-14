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

    def to_json(self):
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "chat_id": self.chat_id,
            "thought": self.thought,
            "context": self.context,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_json(cls, data: Dict):
        return cls(
            user_id=data["user_id"],
            user_name=data["user_name"],
            chat_id=data["chat_id"],
            thought=data["thought"],
            context=data["context"],
            updated_at=data["updated_at"],
        )
