from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List

from aware.communication.primitives.interface.function_detail import FunctionDetail
from aware.chat.parser.json_pydantic_parser import JsonPydanticParser


class Protocol(ABC):
    def __init__(self):
        self.registered_functions: List[FunctionDetail] = []

    def register_function(
        self, name: str, args: Dict[str, Any], description: str, callback: Callable
    ):
        function_detail = FunctionDetail(name, args, description, callback)
        self.registered_functions.append(function_detail)

    # TODO: we need a specific class for function schema!
    def get_functions(self) -> List[Dict[str, Any]]:
        function_schemas = []
        for fn in self.registered_functions:
            function_schemas.append(
                JsonPydanticParser.get_function_schema(
                    name=fn.name,
                    args=fn.args,
                    description=fn.description,
                )
            )
        return function_schemas

    def function_exists(self, name: str) -> bool:
        for fn in self.registered_functions:
            if fn.name == name:
                return True
        return False

    def call_function(self, name: str, **kwargs) -> str:
        for fn in self.registered_functions:
            if fn.name == name:
                try:
                    return fn.callback(**kwargs)
                except Exception as e:
                    raise ValueError(f"Error calling function {name}: {e}")
        raise ValueError(f"Function {name} not registered")

    @abstractmethod
    def setup_functions(self):
        """
        Derived classes must implement this method to set up their specific functions.
        """
        pass
