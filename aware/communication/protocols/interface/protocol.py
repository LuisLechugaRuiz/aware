from abc import ABC, abstractmethod
from typing import Any, Dict, List

from aware.communication.primitives.interface.function_detail import FunctionDetail
from aware.chat.parser.json_pydantic_parser import JsonPydanticParser


class Protocol(ABC):
    def __init__(self, id: str):
        self.id = id
        self.registered_functions: List[FunctionDetail] = []

    # TODO: we need a specific class for function schema!
    def get_functions(self) -> List[Dict[str, Any]]:
        function_schemas = []
        functions = self.setup_functions()
        for fn in functions:
            self.registered_functions.append(fn)
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
                    return f"Error calling function {name}: {e}"
        return f"Function {name} not registered"

    @abstractmethod
    def setup_functions(self) -> List[FunctionDetail]:
        """
        Derived classes must implement this method to set up their specific functions.
        """
        pass
