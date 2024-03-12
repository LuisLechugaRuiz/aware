from dataclasses import dataclass
import json
from typing import Dict, List, Optional

from aware.communication.protocols import (
    TopicPublisher,
    TopicSubscriber,
    ActionClient,
    RequestClient,
)
from aware.communication.protocols import (
    ActionClientConfig,
    ActionServiceConfig,
    EventPublisherConfig,
    EventSubscriberConfig,
    RequestClientConfig,
    RequestServiceConfig,
    TopicPublisherConfig,
    TopicSubscriberConfig,
)
from aware.communication.protocols.interface.input_protocol import InputProtocol
from aware.tool.tool import Tool


@dataclass
class AgentCommunicationConfig:
    action_clients: List[ActionClientConfig]
    action_services: List[ActionServiceConfig]
    event_publishers: List[EventPublisherConfig]
    event_subscribers: List[EventSubscriberConfig]
    request_clients: List[RequestClientConfig]
    request_services: List[RequestServiceConfig]
    topic_publishers: List[TopicPublisherConfig]
    topic_subscribers: List[TopicSubscriberConfig]

    def to_json(self):
        return {
            "action_clients": [client.to_json() for client in self.action_clients],
            "action_services": [service.to_json() for service in self.action_services],
            "event_publishers": [publisher.to_json() for publisher in self.event_publishers],
            "event_subscribers": [subscriber.to_json() for subscriber in self.event_subscribers],
            "request_clients": [client.to_json() for client in self.request_clients],
            "request_services": [service.to_json() for service in self.request_services],
            "topic_publishers": [publisher.to_json() for publisher in self.topic_publishers],
            "topic_subscribers": [subscriber.to_json() for subscriber in self.topic_subscribers],
        }

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        data["action_clients"] = [
            ActionClientConfig.from_json(client) for client in data["action_clients"]
        ]
        data["action_services"] = [
            ActionServiceConfig.from_json(service) for service in data["action_services"]
        ]
        data["event_publishers"] = [
            EventPublisherConfig.from_json(publisher) for publisher in data["event_publishers"]
        ]
        data["event_subscribers"] = [
            EventSubscriberConfig.from_json(subscriber) for subscriber in data["event_subscribers"]
        ]
        data["request_clients"] = [
            RequestClientConfig.from_json(client) for client in data["request_clients"]
        ]
        data["request_services"] = [
            RequestServiceConfig.from_json(service) for service in data["request_services"]
        ]
        data["topic_publishers"] = [
            TopicPublisherConfig.from_json(publisher) for publisher in data["topic_publishers"]
        ]
        data["topic_subscribers"] = [
            TopicSubscriberConfig.from_json(subscriber) for subscriber in data["topic_subscribers"]
        ]
        return cls(**data)


class AgentCommunication:
    def __init__(
        self,
        topic_publishers: Dict[str, TopicPublisher],
        topic_subscribers: Dict[str, TopicSubscriber],
        action_clients: Dict[str, ActionClient],
        request_clients: Dict[str, RequestClient],
        input_protocol: InputProtocol,
    ):
        self.topic_publishers = topic_publishers
        self.topic_subscribers = topic_subscribers
        self.action_clients = action_clients
        self.request_clients = request_clients
        self.input_protocol = input_protocol

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

    def set_input_completed(self):
        self.input_protocol.set_input_completed()

    def to_prompt_kwargs(self) -> Dict[str, str]:
        """Show permanent info on the prompt. Don't show event as it will be part of conversation."""
        prompt_kwargs: Dict[str, str] = {}

        # Add the input
        input = self.input_protocol.get_input()
        prompt_kwargs.update({"input": input.input_to_prompt_string()})

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
