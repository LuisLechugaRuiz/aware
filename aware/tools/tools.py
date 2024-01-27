from abc import ABC, abstractmethod
import json
from typing import Any, Callable, Dict, List, Optional
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
import uuid
import inspect

from aware.data.database.client_handlers import ClientHandlers
from aware.process.process_data import ProcessData
from aware.requests.service import ServiceData


# TODO: Run remote should be a decorator.
class Tools(ABC):
    def __init__(
        self,
        process_data: ProcessData,
        run_remote: bool = False,
    ):
        self.process_data = process_data
        self.run_remote = run_remote
        self.default_tools = self._get_default_tools()

    def create_request(self, service_name: str, query: str):
        return ClientHandlers().create_request(
            self.process_data.ids.user_id,
            self.process_data.ids.process_id,
            service_name,
            query,
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

    def _get_default_tools(self) -> List[Callable]:
        default_tools = []
        if len(self.process_data.requests) > 0:
            default_tools.append(self.set_request_completed)
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

    def update_agent_data(self):
        return ClientHandlers().update_agent_data(
            agent_id=self.process_data.ids.agent_id,
            agent_data=self.process_data.agent_data,
        )

    @abstractmethod
    def set_tools(self) -> List[Callable]:
        pass

    def set_request_completed(self, response: str):
        """Use this method to set the request as completed and provide the response."""

        return ClientHandlers().set_request_completed(
            self.process_data.ids.user_id,
            self.process_data.ids.process_id,
            self.process_data.requests[0].id,
            response,
        )

    def stop_agent(self):
        # TODO: Implement me to stop agent execution, setting it to false at Supabase.
        pass


class FunctionCall:
    def __init__(self, name: str, call_id: str, arguments: Dict[str, Any]):
        self.name = name
        self.call_id = call_id
        self.arguments = arguments
