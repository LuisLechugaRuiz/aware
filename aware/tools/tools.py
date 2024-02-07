from abc import ABC, abstractmethod
import json
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
import uuid
import inspect

from aware.process.process_data import ProcessData
from aware.requests.request import Request
from aware.requests.service import ServiceData

if TYPE_CHECKING:
    from aware.data.database.client_handlers import ClientHandlers


# TODO: Run remote should be a decorator.
class Tools(ABC):
    def __init__(
        self,
        client_handlers: "ClientHandlers",
        process_data: ProcessData,
        run_remote: bool = False,
    ):
        self.client_handlers = client_handlers
        self.process_data = process_data
        self.run_remote = run_remote
        self.request = self._get_current_request()
        self.default_tools = self._get_default_tools()

        self.running = True
        self.async_request_scheduled = False
        self.sync_request_scheduled = False

    def create_async_request(self, service_name: str, query: str):
        self.async_request_scheduled = True

        self.client_handlers.create_request(
            process_ids=self.process_data.ids,
            service_name=service_name,
            query=query,
            is_async=True,
        )
        return "Async request scheduled."

    def create_request(self, service_name: str, query: str):
        self.sync_request_scheduled = True

        return self.client_handlers.create_request(
            process_ids=self.process_data.ids,
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
                f"Default function must have only one argument, {len(args)} were given."
            )
        return {args[0]: content}

    def _get_current_request(self) -> Optional[Request]:
        if len(self.process_data.requests) > 0:
            return self.process_data.requests[0]
        return None

    def _get_default_tools(self) -> List[Callable]:
        default_tools = []
        if self.request is not None:
            default_tools.append(self.set_request_completed)
            if self.request.data.is_async:
                default_tools.append(self.send_feedback)
        # TODO: Do the same with events!!
        return default_tools

    def get_tools(self) -> List[Callable]:
        process_tools = self.set_tools()
        process_tools.extend(self.default_tools)
        return process_tools

    @classmethod
    def get_services(self) -> List[ServiceData]:
        return []

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

    def is_running(self) -> bool:
        return self.running

    def is_async_request_scheduled(self) -> bool:
        return self.async_request_scheduled

    def is_sync_request_scheduled(self) -> bool:
        return self.sync_request_scheduled

    def update_agent_data(self):
        return self.client_handlers.update_agent_data(
            agent_id=self.process_data.ids.agent_id,
            agent_data=self.process_data.agent_data,
        )

    @abstractmethod
    def set_tools(self) -> List[Callable]:
        pass

    def send_feedback(self, feedback: str):
        """Send feedback to the client.

        Args:
            feedback (str): The feedback to send to the client.
        """
        self.request.data.feedback = feedback

        return self.client_handlers.send_feedback(
            request=self.request,
        )

    def set_request_completed(self, response: str):
        """Set request as completed and provide the response to the client.

        Args:
            response (str): The response to the request.
        """
        self.request.data.response = response
        self.request.data.status = "completed"

        return self.client_handlers.set_request_completed(
            user_id=self.process_data.ids.user_id,
            request=self.request,
        )

    def stop_agent(self):
        self.running = False


class FunctionCall:
    def __init__(self, name: str, call_id: str, arguments: Dict[str, Any]):
        self.name = name
        self.call_id = call_id
        self.arguments = arguments
