from abc import ABC, abstractmethod
import json
from typing import Any, Callable, Dict, List, Optional
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
import re
import uuid
import inspect

from aware.agent.database.agent_database_handler import AgentDatabaseHandler
from aware.database.weaviate.memory_manager import MemoryManager
from aware.process.process_info import ProcessInfo
from aware.process.process_handler import ProcessHandler
from aware.utils.logger.process_loger import ProcessLogger
from aware.tools.database.tool_database_handler import ToolDatabaseHandler


class Tools(ABC):
    def __init__(
        self,
        process_info: ProcessInfo,
    ):
        self.process_info = process_info
        self.agent_data = process_info.agent_data
        self.process_ids = process_info.process_ids
        self.process_data = process_info.process_data
        self.process_logger = ProcessLogger(
            user_id=self.process_ids.user_id,
            agent_name=self.agent_data.name,
            process_name=self.process_data.name,
        )
        self.logger = self.process_logger.get_logger(self.get_tool_name())

        self.memory_manager = MemoryManager(
            user_id=self.process_ids.user_id, logger=self.logger
        )
        # TODO: Remove, override by communication handler
        self.process_handler = ProcessHandler()

        self.run_remote = False  # TODO: Make this a decorator for each function!
        self.finished = False  # TODO: Implement this better!

        self.tool_database_handler = ToolDatabaseHandler()

        # TODO: Check where to register capability!! Mode this to registry.
        self.tool_database_handler.create_capability(
            process_ids=self.process_ids, capability_name=self.get_tool_name()
        )
        # TODO: we need a way to update the variable when using a tool. Maybe a wrapper that initializes tool then calls the function and then updates the variable.

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
        if self.process_data.name == "main":
            return self.agent_data.name
        return self.get_tool_name()

    def get_tools(self) -> List[Callable]:
        return self.set_tools()

    @classmethod
    def get_description(cls):
        return cls.__doc__

    @classmethod
    def get_tool_name(cls):
        # Convert class name to snake_case
        return cls.get_snake_case_name(__class__.__name__)

    @classmethod
    def get_snake_case_name(cls, name: str):
        # Convert from CamelCase to snake_case
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        return name

    def get_default_tool_call(
        self, content: str
    ) -> Optional[ChatCompletionMessageToolCall]:
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if (
                callable(attr)
                and hasattr(attr, "is_default_function")
                and getattr(attr, "is_default_function")
            ):
                arguments_dict = self._construct_arguments_dict(attr, content)
                arguments_json = json.dumps(arguments_dict)
                function_call = ChatCompletionMessageToolCall(
                    id=str(uuid.uuid4()),
                    function=Function(arguments=arguments_json, name=attr.__name__),
                    type="function",
                )
                return function_call
        return None

    def is_process_finished(self) -> bool:
        return self.finished

    def update_agent_data(self):
        return AgentDatabaseHandler().update_agent_data(
            agent_data=self.agent_data,
        )

    @abstractmethod
    def set_tools(self) -> List[Callable]:
        pass

    def finish_process(self):
        self.finished = True


class FunctionCall:
    def __init__(self, name: str, call_id: str, arguments: Dict[str, Any]):
        self.name = name
        self.call_id = call_id
        self.arguments = arguments
