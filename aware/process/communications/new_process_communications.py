import json
from dataclasses import dataclass
from typing import List, Optional

# from aware.communications.events.event import Event
# from aware.communications.requests.request import Request
# from aware.communications.topics.topic import Topic

from aware.chat.parser.json_pydantic_parser import JsonPydanticParser
from aware.communications.topics.topic_publisher import TopicPublisher
from aware.communications.topics.topic_subscriber import TopicSubscriber
from aware.communications.requests.request_client import RequestClient
from aware.communications.requests.request_service import RequestService
from aware.communications.events.event_subscriber import EventSubscriber


@dataclass
class ProcessCommunications:
    topic_publishers: List[TopicPublisher]
    topic_subscribers: List[TopicSubscriber]
    request_clients: List[RequestClient]
    request_services: List[RequestService]
    event_subscribers: List[EventSubscriber]

    def to_dict(self):
        return {
            "topic_publishers": [
                topic_publisher.to_dict() for topic_publisher in self.topic_publishers
            ],
            "topic_subscribers": [
                topic_subscriber.to_dict()
                for topic_subscriber in self.topic_subscribers
            ],
            "request_clients": [
                request_client.to_dict() for request_client in self.request_clients
            ],
            "request_services": [
                request_service.to_dict() for request_service in self.request_services
            ],
            "event_subscribers": [
                event_subscriber.to_dict()
                for event_subscriber in self.event_subscribers
            ],
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str: str):
        data = json.loads(json_str)
        data["topic_publishers"] = [
            TopicPublisher(**topic_publisher)
            for topic_publisher in data["topic_publishers"]
        ]
        data["topic_subscribers"] = [
            TopicSubscriber(**topic_subscriber)
            for topic_subscriber in data["topic_subscribers"]
        ]
        data["request_clients"] = [
            RequestClient(**request_client)
            for request_client in data["request_clients"]
        ]
        data["request_services"] = [
            RequestService(**request_service)
            for request_service in data["request_services"]
        ]
        # TODO: should we add event_publisher? Which is the difference between event and topic?
        # I think topic is mean to be used between agents while events is from external world - to agent.
        # This is why agent have only access to event_subscriber and not event_publisher.
        data["event_subscribers"] = [
            EventSubscriber(**event_subscriber)
            for event_subscriber in data["event_subscribers"]
        ]
        return ProcessCommunications(**data)

    def to_functions_str(self):
        functions_str: List[str] = []
        # Get the functions that can be used by agent to communicate with other agents.
        for topic in self.topic_publishers.get_topics():
            # TODO: Should to_function return a Callable or a string directly? Should we use ToolManager (to translate)
            functions_str.append(topic.to_function())
        for request in self.request_clients.get_requests():
            functions_str.append(request.to_function())

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
