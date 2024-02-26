import json
from dataclasses import dataclass
from typing import List, Optional

# from aware.communications.events.event import Event
# from aware.communications.requests.request import Request
# from aware.communications.topics.topic import Topic

from aware.communications.topics.topic_publisher import TopicPublisher
from aware.communications.topics.topic_subscriber import TopicSubscriber
from aware.communications.requests.request_client import RequestClient
from aware.communications.requests.request_service import RequestService
from aware.communications.events.event_subscriber import EventSubscriber


# TODO: REFACTOR ME!!! ADD PUBLISHER/SUBSCRIBER/CLIENTS/SERVERS/EVENTS. NOT DEFINED BY THE KIND OF REQUESTS!!!
@dataclass
class ProcessCommunications:
    topic_publishers: List[TopicPublisher]
    topic_subscribers: List[TopicSubscriber]
    request_clients: List[RequestClient]
    request_services: List[RequestService]
    events_subscribers: List[EventSubscriber]

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
            "events_subscribers": [
                events_subscriber.to_dict()
                for events_subscriber in self.events_subscribers
            ],
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    # TODO: Adapt me!!
    @staticmethod
    def from_json(json_str: str):
        data = json.loads(json_str)
        data["outgoing_requests"] = [
            Request(**request) for request in data["outgoing_requests"]
        ]
        if data["incoming_request"]:
            data["incoming_request"] = Request(**data["incoming_request"])
        if data["event"]:
            data["event"] = Event(**data["event"])
        data["topics"] = [Topic(**topic) for topic in data["topics"]]
        return ProcessCommunications(**data)

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
