from abc import abstractmethod
from dataclasses import dataclass
import re


@dataclass
class Data:
    @classmethod
    @abstractmethod
    def get_identity(cls, **kwargs) -> str:
        pass

    @classmethod
    @abstractmethod
    def get_task(cls, **kwargs) -> str:
        pass

    @classmethod
    def get_instructions(cls, **kwargs) -> str:
        return ""

    @classmethod
    def get_name(cls):
        # Convert from CamelCase to snake_case
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        return name
