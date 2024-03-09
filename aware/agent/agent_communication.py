from typing import Dict, List, Optional

from aware.communication.primitives.interface.input import Input
from aware.communication.protocols import (
    TopicPublisher,
    TopicSubscriber,
    ActionClient,
    RequestClient,
)
from aware.communication.protocols.interface.input_protocol import InputProtocol
from aware.tool.tool import Tool


class AgentCommunication:
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

    def get_tools(self) -> List[Tool]:
        tools: List[Tool] = []
        # Add topic_publisher functions
        for publisher in self.topic_publishers.values():
            tools.extend(publisher.get_tools())
        # Add action_client functions
        for client in self.action_clients.values():
            tools.extend(client.get_tools())
        # Add request_client functions
        for client in self.request_clients.values():
            tools.extend(client.get_tools())

        # Add input protocol functions - Can be request_service, action_service or event_subscriber
        tools.extend(self.input_protocol.get_tools())
        return tools

    def get_publisher(self, topic_name: str) -> Optional[TopicPublisher]:
        return self.topic_publishers.get(topic_name, None)

    def get_client(self, service_name: str) -> Optional[RequestClient]:
        return self.request_clients.get(service_name, None)

    def to_prompt_kwargs(self) -> Dict[str, str]:
        """Show permanent info on the prompt. Don't show event as it will be part of conversation."""
        prompt_kwargs: Dict[str, str] = {}

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
