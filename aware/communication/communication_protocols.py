import json
from typing import Any, Dict, List, Optional
from openai.types.chat import ChatCompletionMessageToolCall

from aware.communication.primitives.interface.input import Input
from aware.communication.protocols import (
    TopicPublisher,
    TopicSubscriber,
    ActionClient,
    RequestClient,
)
from aware.communication.protocols.interface.input_protocol import InputProtocol


class CommunicationProtocols:
    def __init__(
        self,
        topic_publishers: Dict[str, TopicPublisher],
        topic_subscribers: Dict[str, TopicSubscriber],
        action_clients: Dict[str, ActionClient],
        request_clients: Dict[str, RequestClient],
    ):
        self.topic_publishers = topic_publishers
        self.topic_subscribers = topic_subscribers
        self.action_clients = action_clients
        self.request_clients = request_clients
        self.input_protocol = None
        self.input = None

    def add_input(self, input: Input, input_protocol: InputProtocol):
        self.input = input
        self.input_protocol = input_protocol

    def to_dict(self):
        return {
            "topic_publishers": {
                topic_name: topic_publisher.to_dict()
                for topic_name, topic_publisher in self.topic_publishers.items()
            },
            "topic_subscribers": {
                topic_name: topic_subscriber.to_dict()
                for topic_name, topic_subscriber in self.topic_subscribers.items()
            },
            "action_clients": {
                action_name: action_client.to_dict()
                for action_name, action_client in self.action_clients.items()
            },
            "request_clients": {
                service_name: request_client.to_dict()
                for service_name, request_client in self.request_clients.items()
            },
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str: str):
        data = json.loads(json_str)
        data["topic_publishers"] = {
            topic_name: TopicPublisher(**topic_publisher)
            for topic_name, topic_publisher in data["topic_publishers"].items()
        }
        data["topic_subscribers"] = {
            topic_name: TopicSubscriber(**topic_subscriber)
            for topic_name, topic_subscriber in data["topic_subscribers"].items()
        }
        data["action_clients"] = {
            action_name: ActionClient(**action_client)
            for action_name, action_client in data["action_clients"].items()
        }
        data["request_clients"] = {
            request_name: RequestClient(**request_client)
            for request_name, request_client in data["request_clients"].items()
        }
        return CommunicationProtocols(**data)

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
        if self.input_protocol:
            function_schemas.extend(self.input_protocol.get_functions())
        return function_schemas

    # TODO: we want to extract here if we need to continue processing or not,
    #   i.e: call_function might means scheduling request, in that case we want to stop. Check ProcessToolCallResponse from communication_handler.py and remove it once we achieve this.
    # TODO: make this more elegant.
    def call_function(
        self, function_name: str, function_args: Dict[str, Any]
    ) -> Optional[str]:

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
        if self.input_protocol:
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
        if self.input:
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
