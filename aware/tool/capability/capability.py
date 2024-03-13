from abc import ABC, abstractmethod
import json
from typing import Callable, List, Optional
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
import re
import uuid
import inspect

from aware.agent.database.agent_database_handler import AgentDatabaseHandler
from aware.chat.database.chat_database_handler import ChatDatabaseHandler
from aware.utils.parser.pydantic_parser import PydanticParser
from aware.database.weaviate.memory_manager import MemoryManager
from aware.process.process_info import ProcessInfo
from aware.utils.logger.process_logger import ProcessLogger
from aware.tool.decorators import IS_DEFAULT_FUNCTION, IS_TOOL
from aware.tool.tool import Tool


class Capability(ABC):
    def __init__(
        self,
        process_info: ProcessInfo,
    ):
        self.process_info = process_info
        self.agent_data = process_info.agent_data
        self.process_ids = process_info.process_ids
        self.process_data = process_info.process_data
        self.process_logger = ProcessLogger(
            user_id=self.process_ids.user_id, agent_name=process_info.agent_data.name, process_name=process_info.process_data.name
        )
        self.logger = self.process_logger.get_logger(self.get_name())

        self.memory_manager = MemoryManager(
            user_id=self.process_ids.user_id, logger=self.logger
        )
        self.chat_database_handler = ChatDatabaseHandler(self.process_logger)

        # TODO: we need a way to update the variable when using a tool. Maybe a wrapper that initializes tool then calls the function and then updates the variable.
        # TODO: vars = self.get_capability_vars() # Use it to hold internal state of each capability.
        # TODO: selt.iterations = vars[iterations]
        self.iterations = 0

    def _construct_arguments_dict(self, func: Callable, content: str):
        signature = inspect.signature(func)
        args = list(signature.parameters.keys())
        if not args:
            raise ValueError("Default function must have one argument.")
        if len(args) > 1:
            raise ValueError(
                f"Default function must have only one argument, {len(args)} wer1e given."
            )
        return {args[0]: content}

    def get_process_name(self) -> str:
        return self.process_data.name

    @classmethod
    def get_description(cls):
        return cls.__doc__

    @classmethod
    def get_name(cls):
        # Convert class name to snake_case
        return cls.get_snake_case_name(__class__.__name__)

    @classmethod
    def get_snake_case_name(cls, name: str):
        # Convert from CamelCase to snake_case
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        return name

    def _get_callables(self, attribute_name: str) -> List[Callable]:
        callables: List[Callable] = []
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if (
                callable(attr)
                and hasattr(attr, attribute_name)
                and getattr(attr, attribute_name)
            ):
                callables.append(attr)
        return callables

    def get_filtered_tools(self, tool_names: List[str]) -> List[Tool]:
        return [tool for tool in self.get_tools() if tool.name in tool_names]

    def get_tools(self) -> List[Tool]:
        callables = self._get_callables(attribute_name=IS_TOOL)

        return [PydanticParser.get_tool(callable) for callable in callables]

    def get_default_tool_call(
        self, content: str
    ) -> Optional[ChatCompletionMessageToolCall]:
        callables = self._get_callables(IS_DEFAULT_FUNCTION)
        if len(callables) > 0:
            attr = callables[0]  # This assumes only one default function.
            arguments_dict = self._construct_arguments_dict(attr, content)
            arguments_json = json.dumps(arguments_dict)
            function_call = ChatCompletionMessageToolCall(
                id=str(uuid.uuid4()),
                function=Function(arguments=arguments_json, name=attr.__name__),
                type="function",
            )
            return function_call
        return None

    def update_agent_data(self):
        return AgentDatabaseHandler(self.process_ids.user_id).update_agent_data(
            agent_data=self.agent_data,
        )
