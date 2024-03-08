import json
from typing import Any, Dict, List, Optional
from openai.types.chat import ChatCompletionMessageToolCall

from aware.communication.helpers.communication_result import CommunicationResult
from aware.communication.primitives.interface.input import Input
from aware.communication.protocols import (
    TopicPublisher,
    TopicSubscriber,
    ActionClient,
    RequestClient,
)
from aware.communication.protocols.interface.input_protocol import InputProtocol


# The only reason to create CommunicationProtocols is because there is an input that needs to be processed. Otherwise we should not need to get it, verify this hypothesis.
class CommunicationProtocols:
    def __init__(
        self,
        topic_publishers: Dict[str, TopicPublisher],
        topic_subscribers: Dict[str, TopicSubscriber],
        action_clients: Dict[str, ActionClient],
        request_clients: Dict[str, RequestClient],
        input_protocol: InputProtocol,
        input: Input,
    ):
        self.topic_publishers = topic_publishers
        self.topic_subscribers = topic_subscribers
        self.action_clients = action_clients
        self.request_clients = request_clients
        self.input_protocol = input_protocol
        self.input = input

    def get_function_schemas(self) -> List[Dict[str, Any]]:
        function_schemas: List[Dict[str, Any]] = []
        # Add topic_publisher functions
        for publisher in self.topic_publishers.values():
            function_schemas.extend(publisher.get_functions())
        # Add action_client functions
        for client in self.action_clients.values():
            function_schemas.extend(client.get_functions())
        # Add request_client functions
        for client in self.request_clients.values():
            function_schemas.extend(client.get_functions())

        # Add input protocol functions - Can be request_service, action_service or event_subscriber
        function_schemas.extend(self.input_protocol.get_functions())
        return function_schemas

    # TODO: make this more elegant.
    def process_tool_call(
        self, tool_call: ChatCompletionMessageToolCall
    ) -> Optional[CommunicationResult]:
        function_name = tool_call.function.name
        function_args = self.tool_call_to_args(tool_call)

        # Output protocols
        for publisher in self.topic_publishers.values():
            if function_name == publisher.function_exists(function_name):
                return publisher.call_function(function_name, function_args)
        for client in self.request_clients.values():
            if function_name == client.function_exists(function_name):
                return client.call_function(function_name, function_args)
        for client in self.action_clients.values():
            if function_name == client.function_exists(function_name):
                return client.call_function(function_name, function_args)

        # Input protocol
        if function_name == self.input_protocol.function_exists(function_name):
            return self.input_protocol.call_function(function_name, function_args)
        return None

    def get_publisher(self, topic_name: str) -> Optional[TopicPublisher]:
        return self.topic_publishers.get(topic_name, None)

    def get_client(self, service_name: str) -> Optional[RequestClient]:
        return self.request_clients.get(service_name, None)

    def to_prompt_kwargs(self):
        """Show permanent info on the prompt. Don't show event as it will be part of conversation."""
        prompt_kwargs = {}

        # Add the input
        prompt_kwargs.update({"input": self.input.input_to_prompt_string()})

        # Add the feedback of all the client actions
        actions_feedback = "\n".join(
            [clients.get_action_feedback() for clients in self.action_clients.values()]
        )
        prompt_kwargs.update({"actions_feedback": actions_feedback})

        topic_updates = "\n".join(
            [
                topic_subscriber.get_topic_update()
                for topic_subscriber in self.topic_subscribers.values()
            ]
        )
        prompt_kwargs.update({"topics": "\n".join(topic_updates)})
        return prompt_kwargs

    def tool_call_to_args(
        self, tool_call: ChatCompletionMessageToolCall
    ) -> Dict[str, Any]:
        return json.loads(tool_call.function.arguments)
