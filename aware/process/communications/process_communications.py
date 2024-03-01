import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# from aware.communications.events.event import Event
# from aware.communications.requests.request import Request
# from aware.communications.topics.topic import Topic

from aware.communications.topics.topic_publisher import TopicPublisher
from aware.communications.topics.topic_subscriber import TopicSubscriber
from aware.communications.requests.request_client import RequestClient
from aware.communications.requests.request_service import RequestService
from aware.communications.events.event_subscriber import EventSubscriber


@dataclass
class ProcessCommunications:
    topic_publishers: Dict[str, TopicPublisher]
    topic_subscribers: Dict[str, TopicSubscriber]
    request_clients: Dict[str, RequestClient]
    request_services: Dict[str, RequestService]
    event_subscribers: Dict[str, EventSubscriber]

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
            "request_clients": {
                request_name: request_client.to_dict()
                for request_name, request_client in self.request_clients.items()
            },
            "request_services": {
                request_name: request_service.to_dict()
                for request_name, request_service in self.request_services.items()
            },
            "event_subscribers": {
                event_name: event_subscriber.to_dict()
                for event_name, event_subscriber in self.event_subscribers.items()
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
        data["request_clients"] = {
            request_name: RequestClient(**request_client)
            for request_name, request_client in data["request_clients"].items()
        }
        data["request_services"] = {
            request_name: RequestService(**request_service)
            for request_name, request_service in data["request_services"].items()
        }
        # TODO: should we add event_publisher? Which is the difference between event and topic?
        # I think topic is mean to be used between agents while events is from external world - to agent.
        # This is why agent have only access to event_subscriber and not event_publisher.
        data["event_subscribers"] = {
            event_name: EventSubscriber(**event_subscriber)
            for event_name, event_subscriber in data["event_subscribers"].items()
        }
        return ProcessCommunications(**data)

    def get_function_schemas(self):
        function_schemas: List[Dict[str, Any]] = []
        for publisher in self.topic_publishers.values():
            function_schemas.append(publisher.get_topic_as_function())
        for client in self.request_clients.values():
            function_schemas.append(client.get_request_as_function())
        return function_schemas

    def get_publisher_topic_id(self, topic_name: str) -> Optional[str]:
        publisher = self.topic_publishers.get(topic_name, None)
        if publisher is None:
            return None
        return publisher.topic_id

    def get_client_service_id(self, service_name: str) -> Optional[str]:
        client = self.request_clients.get(service_name, None)
        if client is None:
            return None
        return client.service_id

    # TODO: Get right requests from client/servers and data from pub/sub, TBD.
    def to_prompt_kwargs(self):
        """Show permanent info on the prompt. Don't show event as it will be part of conversation."""
        prompt_kwargs = {}
        if self.outgoing_requests:
            # Add the feedback of all the outgoing requests
            requests_feedback = "\n".join(
                [request.feedback_to_string() for request in self.outgoing_requests]
            )
            prompt_kwargs.update({"outgoing_requests": requests_feedback})
        if self.incoming_request is not None:
            # Add the query of the incoming request
            prompt_kwargs.update(
                {"incoming_request": self.incoming_request.query_to_string()}
            )
        if self.topics:
            topics_info = "\n".join([topic.to_string() for topic in self.topics])
            prompt_kwargs.update({"topics": topics_info})
        return prompt_kwargs
