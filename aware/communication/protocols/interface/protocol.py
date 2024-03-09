from abc import ABC, abstractmethod
from typing import List

from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)
from aware.communication.primitives.interface.function_detail import FunctionDetail
from aware.chat.parser.json_pydantic_parser import JsonPydanticParser
from aware.tool.tool import Tool


class Protocol(ABC):
    def __init__(self, id: str):
        self.id = id
        self.primitive_database_handler = PrimitivesDatabaseHandler()

    def get_tools(self) -> List[Tool]:
        tools: List[Tool] = []
        for fn in self.communication_functions:
            tools.append(
                JsonPydanticParser.get_tool(
                    name=fn.name,
                    args=fn.args,
                    description=fn.description,
                )
            )
        return tools

    @abstractmethod
    @property
    def communication_functions(self) -> List[FunctionDetail]:
        """
        Derived classes must implement this method to set up their specific functions.
        """
        pass
