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

from aware.data.database.client_handlers import ClientHandlers
from aware.memory.memory_manager import MemoryManager
from aware.process.process_info import ProcessInfo
from aware.process.process_handler import ProcessHandler
from aware.utils.logger.file_logger import FileLogger


class Tools(ABC):
    def __init__(
        self,
        process_info: ProcessInfo,
    ):
        self.agent_data = process_info.agent_data
        self.process_ids = process_info.process_ids
        self.process_data = process_info.process_data
        self.request = process_info.process_communications.incoming_request

        self.logger = FileLogger(process_info.get_name())

        self.default_tools = self._get_default_tools()
        self.memory_manager = MemoryManager(
            user_id=self.process_ids.user_id, logger=self.logger
        )
        self.process_handler = ProcessHandler()

        self.run_remote = False  # TODO: Make this a decorator for each function!
        self.finished = False
        self.async_request_scheduled = False
        self.sync_request_scheduled = False

    def create_async_request(self, service_name: str, query: str):
        self.async_request_scheduled = True

        self.process_handler.create_request(
            client_process_name=self.get_process_name(),
            client_process_ids=self.process_ids,
            service_name=service_name,
            query=query,
            is_async=True,
        )
        return "Async request scheduled."

    def create_request(self, service_name: str, query: str):
        self.sync_request_scheduled = True

        return self.process_handler.create_request(
            client_process_name=self.get_process_name(),
            client_process_ids=self.process_ids,
            service_name=service_name,
            query=query,
            is_async=False,
        )

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

    def _get_default_tools(self) -> List[Callable]:
        default_tools = []
        if self.request is not None:
            default_tools.append(self.set_request_completed)
            if self.request.is_async():
                default_tools.append(self.send_feedback)
        return default_tools

    def get_process_name(self) -> str:
        if self.process_data.name == "main":
            return self.agent_data.name
        return self.get_tool_name()

    def get_tools(self) -> List[Callable]:
        process_tools = self.set_tools()
        process_tools.extend(self.default_tools)
        return process_tools

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

    def is_async_request_scheduled(self) -> bool:
        return self.async_request_scheduled

    def is_sync_request_scheduled(self) -> bool:
        return self.sync_request_scheduled

    def update_agent_data(self):
        return ClientHandlers().update_agent_data(
            agent_data=self.agent_data,
        )

    @abstractmethod
    def set_tools(self) -> List[Callable]:
        pass

    def send_feedback(self, feedback: str):
        """Send feedback to the client.

        Args:
            feedback (str): The feedback to send to the client.
        """
        return ClientHandlers().update_request_feedback(
            request=self.request, feedback=feedback
        )

    def set_request_completed(self, response: str, success: bool):
        """Set request as completed and provide the response to the client.

        Args:
            response (str): The response to the request.
        """
        self.process_handler.set_request_completed(
            request=self.request, response=response, success=success
        )

    def finish_process(self):
        self.finished = True


class FunctionCall:
    def __init__(self, name: str, call_id: str, arguments: Dict[str, Any]):
        self.name = name
        self.call_id = call_id
        self.arguments = arguments
