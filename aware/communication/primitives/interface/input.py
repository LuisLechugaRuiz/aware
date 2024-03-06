from abc import ABC, abstractmethod


# TODO: Fill me properly.
class Input(ABC):
    def __init__(self, priority: int):
        self.priority = priority

    @abstractmethod
    def is_completed(self) -> bool:
        pass
