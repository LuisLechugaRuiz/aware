from abc import ABC, abstractmethod

from aware.chat.conversation_schemas import UserMessage


class Input(ABC):
    def __init__(self, id: str, priority: int):
        self.id = id
        self.priority = priority

    @abstractmethod
    def get_type(self) -> str:
        pass

    @abstractmethod
    def input_to_prompt_string(self) -> str:
        pass

    @abstractmethod
    def input_to_user_message(self) -> UserMessage:
        pass

    @abstractmethod
    def is_completed(self) -> bool:
        pass
