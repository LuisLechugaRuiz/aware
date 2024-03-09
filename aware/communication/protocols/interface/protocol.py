from abc import ABC, abstractmethod
from typing import Any, Dict, List

from aware.communication.helpers.communication_result import CommunicationResult
from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)
from aware.communication.primitives.interface.function_detail import FunctionDetail
from aware.chat.parser.json_pydantic_parser import JsonPydanticParser


class Protocol(ABC):
    def __init__(self, id: str):
        self.id = id
        self.registered_functions: List[FunctionDetail] = []
        self.primitive_database_handler = PrimitivesDatabaseHandler()

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        openai_tools = []
        functions = self.setup_functions()
        for fn in functions:
            self.registered_functions.append(fn)
            openai_tools.append(
                JsonPydanticParser.get_openai_tool(
                    name=fn.name,
                    args=fn.args,
                    description=fn.description,
                )
            )
        return openai_tools

    def function_exists(self, name: str) -> bool:
        for fn in self.registered_functions:
            if fn.name == name:
                return True
        return False

    def call_function(self, name: str, **kwargs) -> CommunicationResult:
        for fn in self.registered_functions:
            if fn.name == name:
                try:
                    return CommunicationResult(
                        fn.callback(**kwargs), should_continue=fn.should_continue
                    )
                except Exception as e:
                    return CommunicationResult(
                        result=f"Error calling function {name}: {e}",
                        should_continue=True,
                    )
        return CommunicationResult(
            result=f"Function {name} not registered", should_continue=True
        )

    @abstractmethod
    def setup_functions(self) -> List[FunctionDetail]:
        """
        Derived classes must implement this method to set up their specific functions.
        """
        pass
