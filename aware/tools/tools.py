from abc import ABC, abstractmethod
import json
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
import re
import uuid
import inspect

from aware.agent.agent_data import AgentData
from aware.chat.conversation_schemas import UserMessage, ToolResponseMessage
from aware.communications.requests.request import Request
from aware.communications.requests.service import ServiceData
from aware.process.process_ids import ProcessIds
from aware.process.process_data import ProcessData
from aware.process.process_handler import ProcessHandler

if TYPE_CHECKING:
    from aware.data.database.client_handlers import ClientHandlers


# TODO: Run remote should be a decorator.
class Tools(ABC):
    def __init__(
        self,
        client_handlers: "ClientHandlers",
        process_ids: ProcessIds,
        process_data: ProcessData,
        agent_data: AgentData,
        request: Optional[Request],
        run_remote: bool = False,
    ):
        self.client_handlers = client_handlers

        self.process_ids = process_ids
        self.process_data = process_data
        self.agent_data = agent_data
        self.request = request

        self.default_tools = self._get_default_tools()

        self.run_remote = run_remote
        self.running = True
        self.async_request_scheduled = False
        self.sync_request_scheduled = False

    def create_async_request(self, service_name: str, query: str):
        self.async_request_scheduled = True

        self.client_handlers.create_request(
            process_ids=self.process_ids,
            service_name=service_name,
            query=query,
            is_async=True,
        )
        return "Async request scheduled."

    def create_request(self, service_name: str, query: str):
        self.sync_request_scheduled = True

        return self.client_handlers.create_request(
            process_ids=self.process_ids,
            service_name=service_name,
            query=query,
            is_async=False,
        )

    def _create_request(self, service_name: str, query: str, is_async: bool):
        request = self.client_handlers.create_request(
            process_ids=self.process_ids,
            service_name=service_name,
            query=query,
            is_async=is_async,
        )
        redis_handler = ClientHandlers().get_redis_handler()
        # Get agent id from process_id
        service_agent_id = redis_handler.get_agent_id_by_process_id(
            request.service_process_id
        )
        server_process_ids = ProcessIds(
            user_id=self.process_ids.user_id,
            agent_id=service_agent_id,
            process_id=request.service_process_id,
        )
        if not redis_handler.is_process_active(server_process_ids):
            # Start server process if not running
            server_process_handler = ProcessHandler(process_ids=server_process_ids)
            # TODO: Verify we want to call on_transition or explicitely start!
            server_process_handler.on_transition()

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
        # TODO: Do the same with events!!
        return default_tools

    def get_tools(self) -> List[Callable]:
        process_tools = self.set_tools()
        process_tools.extend(self.default_tools)
        return process_tools

    @classmethod
    def get_process_name(cls):
        # Convert from CamelCase to snake_case
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__class__.__name__).lower()
        return name

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
            agent_id=self.process_ids.agent_id,
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

        redis_handler = ClientHandlers().get_redis_handler()
        client_agent_id = redis_handler.get_agent_id_by_process_id(
            self.request.client_process_id
        )
        client_process_ids = ProcessIds(
            user_id=self.process_ids.user_id,
            agent_id=client_agent_id,
            process_id=self.request.client_process_id,
        )
        client_process_handler = ProcessHandler(process_ids=client_process_ids)

        # Add message to client process.
        if self.request.is_async():
            # - Async requests: Add new message with the response.
            client_process_handler.add_message(
                json_message=UserMessage(name=self.process_data.name, content=response)
            )
        else:
            # - Sync requests: Update last conversation message with the response.
            client_conversation_with_keys = redis_handler.get_conversation_with_keys(
                self.request.client_process_id
            )
            message_key, message = client_conversation_with_keys[-1]
            if not isinstance(message, ToolResponseMessage):
                raise ValueError("Last message is not a tool response message.")
            message.content = self.request.data.response
            redis_handler.update_message(message_key, message)

        # TODO: Verify this. On transition will change the state of the process even if it is already running...
        client_process_handler.on_transition()

        return self.client_handlers.set_request_completed(
            request=self.request,
        )

    def stop_agent(self):
        self.running = False


class FunctionCall:
    def __init__(self, name: str, call_id: str, arguments: Dict[str, Any]):
        self.name = name
        self.call_id = call_id
        self.arguments = arguments
