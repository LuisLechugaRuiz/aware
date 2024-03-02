import json
from enum import Enum
from typing import Any, Dict
from openai.types.chat import ChatCompletionMessageToolCall

from aware.chat.conversation_schemas import UserMessage, ToolResponseMessage
from aware.communications.communications import Communications
from aware.data.database.client_handlers import ClientHandlers
from aware.process.process_ids import ProcessIds
from aware.process.process_handler import ProcessHandler


class ProcessToolCallResponse(Enum):
    SYNC_REQUEST_SCHEDULED = 1
    ASYNC_REQUEST_SCHEDULED = 2
    TOPIC_UPDATE_SCHEDULED = 3
    REQUEST_RESPONSE_SCHEDULED = 4
    REQUEST_FEEDBACK_SCHEDULED = 5
    NOT_COMMUNICATION_SCHEDULED = 6


class CommunicationsHandler:
    def __init__(
        self,
        process_ids: ProcessIds,
        communications: Communications,
    ):
        self.process_ids = process_ids
        self.communications = communications
        self.current_request = self.communications.get_highest_prio_request()

        self.process_handler = ProcessHandler()

    def create_request(
        self,
        function_call_id: str,
        service_id: str,
        client_id: str,
        client_process_name: str,
        request_message: Dict[str, Any],
        priority: int,
        is_async: bool,
    ) -> str:
        # - Save request in database
        result = ClientHandlers().create_request(
            user_id=self.process_ids.user_id,
            service_id=service_id,
            client_id=client_id,
            client_process_id=self.process_ids.process_id,
            client_process_name=client_process_name,
            request_message=request_message,
            priority=priority,
            is_async=is_async,
        )
        if result.error:
            error = f"Error creating request: {result.error}"
            request_error_response = ToolResponseMessage(
                content=error, tool_call_id=function_call_id
            )
            self.process_handler.add_message(
                process_ids=self.process_ids, message=request_error_response
            )
            return error

        request = result.data
        if is_async:
            acknowledge = f"Request {request.id} created successfully"
            request_ack_response = ToolResponseMessage(
                content=acknowledge, tool_call_id=function_call_id
            )
            self.process_handler.add_message(
                process_ids=self.process_ids, message=request_ack_response
            )

        self.process_handler.process_request(request)

        # - Start the service process if not running
        request = result.data
        service_process_ids = ClientHandlers().get_process_ids(
            process_id=request.service_process_id
        )
        self.process_handler.start(service_process_ids)
        return f"Request {request.id} created successfully"

    def publish_message(self, topic_name: str, message: Dict[str, Any]) -> str:
        # TODO: implement me.
        return ClientHandlers().publish_message(
            topic_name=topic_name,
            message=message,
        )

    def set_request_completed(self, response: Dict[str, Any], success: bool):
        """Set request as completed and provide the response to the client."""
        service_process_name = (
            ClientHandlers()
            .get_process_data(self.current_request.service_process_id)
            .name
        )

        redis_handler = ClientHandlers().get_redis_handler()
        client_process_ids = (
            ClientHandlers()
            .get_process_info(self.current_request.client_process_id)
            .process_ids
        )

        # Add message to client process.
        if self.current_request.is_async():
            content = "\n".join([f"{key}: {value}" for key, value in response.items()])
            # - Async requests: Add new message with the response and start the client process.
            self.process_handler.add_message(
                process_ids=client_process_ids,
                json_message=UserMessage(name=service_process_name, content=content),
            )
            self.process_handler.start(process_ids=client_process_ids)
        else:
            # - Sync requests: Update last conversation message with the response and step (continue from current state) the client process.
            client_conversation_with_keys = redis_handler.get_conversation_with_keys(
                self.current_request.client_process_id
            )
            message_key, message = client_conversation_with_keys[-1]
            if not isinstance(message, ToolResponseMessage):
                raise ValueError("Last message is not a tool response message.")
            message.content = self.current_request.data.response
            redis_handler.update_message(message_key, message)
            # TODO: Refine this logic, we should have more control over agents that are waiting for a response, split between the current transition and the state.
            self.process_handler.step(process_ids=client_process_ids)

        return ClientHandlers().set_request_completed(
            request=self.current_request, success=success, response=response
        )

    def send_feedback(self, feedback: Dict[str, Any]):
        """Send feedback to the client.

        Args:
            feedback (str): The feedback to send to the client.
        """
        return ClientHandlers().update_request_feedback(
            request=self.current_request, feedback=feedback
        )

    def process_tool_call(
        self, process_name: str, tool_call: ChatCompletionMessageToolCall
    ) -> ProcessToolCallResponse:
        tool_name = tool_call.function.name
        client = self.communications.get_client(service_name=tool_name)
        topic_id = self.communications.get_publisher_topic_id(topic_name=tool_name)

        function_args = self.tool_call_to_args(tool_call)
        if client is not None:
            is_async = function_args.pop("is_async")
            priority = function_args.pop("priority")
            self.create_request(
                function_call_id=tool_call.id,
                service_id=client.service_id,
                client_id=client.client_id,
                client_process_name=process_name,
                request_message=function_args,
                priority=priority,
                is_async=is_async,
            )
            if is_async:
                return ProcessToolCallResponse.ASYNC_REQUEST_SCHEDULED
            return ProcessToolCallResponse.SYNC_REQUEST_SCHEDULED
        elif topic_id is not None:
            self.publish_message(topic_name=tool_name, message=function_args)
            return ProcessToolCallResponse.TOPIC_UPDATE_SCHEDULED
        elif tool_name == self.set_request_completed.__name__:
            success = function_args.pop("success")
            self.set_request_completed(response=function_args, success=success)
            return ProcessToolCallResponse.REQUEST_RESPONSE_SCHEDULED
        elif tool_name == self.send_feedback.__name__:
            self.send_feedback(feedback=function_args)
            return ProcessToolCallResponse.REQUEST_FEEDBACK_SCHEDULED
        return ProcessToolCallResponse.NOT_COMMUNICATION_SCHEDULED

    # TODO: Verify me!
    def tool_call_to_args(
        self, tool_call: ChatCompletionMessageToolCall
    ) -> Dict[str, Any]:
        return json.loads(tool_call.function.arguments)

    # Functions used by process to fill the prompt and get communications as tools.
    def get_function_schemas(self):
        return self.communications.get_function_schemas()

    def to_prompt_kwargs(self):
        return self.communications.to_prompt_kwargs()
