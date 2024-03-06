import json
from enum import Enum
from typing import Any, Dict
from openai.types.chat import ChatCompletionMessageToolCall

from aware.chat.conversation_schemas import UserMessage, ToolResponseMessage
from aware.communication.communication_protocols import CommunicationProtocols
from aware.communication.protocols.request_client import RequestClient
from aware.communication.protocols.request_service import RequestService
from aware.communication.protocols.topic_publisher import TopicPublisher

# TODO: Remove.
from aware.data.database.client_handlers import ClientHandlers


from aware.process.process_ids import ProcessIds
from aware.process.process_handler import ProcessHandler
from aware.utils.logger.process_loger import ProcessLogger


class ProcessToolCallResponse(Enum):
    SYNC_REQUEST_SCHEDULED = 1
    ASYNC_REQUEST_SCHEDULED = 2
    TOPIC_UPDATE_SCHEDULED = 3
    REQUEST_RESPONSE_SCHEDULED = 4
    REQUEST_FEEDBACK_SCHEDULED = 5
    NOT_COMMUNICATION_SCHEDULED = 6


# TODO: Refactor! Move logic to specific protocols.
class CommunicationHandler:
    def __init__(
        self,
        process_ids: ProcessIds,
        communication_protocols: CommunicationProtocols,
        process_logger: ProcessLogger,
    ):
        self.process_ids = process_ids
        self.communication_protocols = communication_protocols

        self.process_handler = ProcessHandler(process_logger)
        self.logger = process_logger.get_logger("communication_handler")

    def create_request(
        self,
        client: RequestClient,
        function_args: Dict[str, Any],
        function_call_id: str,
    ) -> str:
        priority = function_args.pop("priority")
        self.logger.info(
            f"Creating request on service: {client.service_id} with message: {function_args} - priority: {priority} - is_async: {is_async}"
        )
        # - Save request in database
        result = client.create_request(
            request_message=function_args,
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
            self.logger.error(error)
            return error

        request = result.data
        acknowledge = f"Request {request.id} created successfully"
        if is_async:
            request_ack_response = ToolResponseMessage(
                content=acknowledge, tool_call_id=function_call_id
            )
            self.process_handler.add_message(
                process_ids=self.process_ids, message=request_ack_response
            )
            self.logger.info(acknowledge)

        # TODO: REFACTOR THIS! We should just send the request to be processed. We should split logic - Process that is being used and the process that could be active due to new request.
        self.process_handler.process_request(request)
        return acknowledge

    # Are events dependent on user_id?
    # Events should come from external sources which are agnostic of our internal structure.... How do we know which user_id to use...?
    # Are all events the same for all users? Do this even make sense? Maybe users should live at Organization level and events should be available for all of them..
    # TODO: This create_event should be part of Publisher... we should split the logic, publisher, subscribers.. are the ones that should contain the methods to manage internal requests. Then we need another logic to trigger certain processes at system level... to be considered..
    def create_event(self, publisher_id: str, event_message: Dict[str, Any]):
        self.logger.info(
            f"Creating event for publisher: {publisher_id} with message: {event_message}"
        )
        # - Add event to database
        event = ClientHandlers().create_event(
            publisher_id=publisher_id,
            event_message=event_message,
        )
        self.logger.info("Event created on database")
        # - Trigger the subscribed processes - based on event_type_id!!
        processes_ids = ClientHandlers().get_events(user_id=user_id, event=event)
        self.logger.info(f"Processes subscribed to event: {processes_ids}")
        for process_ids in processes_ids:
            self.start(process_ids)

    def update_topic(
        self,
        topic_publisher: TopicPublisher,
        message: Dict[str, Any],
        function_call_id: str,
    ) -> str:
        topic_publisher.update_topic(
            message=message,
        )
        acknowledge = "Topic updated successfully"
        request_ack_response = ToolResponseMessage(
            content=acknowledge, tool_call_id=function_call_id
        )
        self.process_handler.add_message(
            process_ids=self.process_ids, message=request_ack_response
        )
        self.logger.info(acknowledge)

    # TODO: REMOVE! It has been implemented at RequestService and now we get it using Protocol abstraction.
    def set_request_completed(self, function_args: Dict[str, Any]):
        """Set request as completed and provide the response to the client."""
        success = function_args.pop("success")

        # Current service request
        request = self.communication_protocols.service_request

        # Set request completed on database.
        service_name = request.service_name
        service = self.communication_protocols.get_service(service_name)
        service.set_request_completed(response=function_args, success=success)

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

    # TODO: Instead of calling raw functions what we need is:
    # Split between client / services (more general names to include publisher vs subscribers).
    # Check all "clients" and call get_functions over them.
    # Check only the current protocol that is being used to manage the current input and check the functions.
    def process_tool_call(
        self, tool_call: ChatCompletionMessageToolCall
    ) -> ProcessToolCallResponse:
        tool_name = tool_call.function.name
        client = self.communication_protocols.get_client(service_name=tool_name)
        publisher = self.communication_protocols.get_publisher(topic_name=tool_name)

        function_args = self.tool_call_to_args(tool_call)
        function_response = self.communication_protocols.call_function(
            tool_name, function_args
        )
        # TODO: how to return the proper ProcessToolCallResponse?
        if function_response is None:
            return ProcessToolCallResponse.NOT_COMMUNICATION_SCHEDULED

        # TODO: Old one!! REMOVE.
        if client is not None:
            is_async = function_args["is_async"]  # TODO: remove, refactor!
            self.create_request(client, function_args, tool_call.id)
            if is_async:
                return ProcessToolCallResponse.ASYNC_REQUEST_SCHEDULED
            return ProcessToolCallResponse.SYNC_REQUEST_SCHEDULED
        elif publisher is not None:
            self.update_topic(publisher, function_args, tool_call.id)
            return ProcessToolCallResponse.TOPIC_UPDATE_SCHEDULED
        elif tool_name == self.set_request_completed.__name__:
            self.set_request_completed(function_args)
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

    def get_function_schemas(self):
        return self.communication_protocols.get_function_schemas()

    def to_prompt_kwargs(self):
        return self.communication_protocols.to_prompt_kwargs()
