from abc import ABC, abstractmethod


# TODO: Fill me properly.
# TODO: How to get kwarg prompts from input? Maybe abstract function to fill it.
class Input(ABC):
    def __init__(self, priority: int):
        self.priority = priority

    @abstractmethod
    def is_completed(self) -> bool:
        pass

    @abstractmethod
    def input_to_prompt_string(self) -> str:
        pass
