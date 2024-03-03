import json
from typing import Any, Dict, List, Optional

# from aware.communications.events.event import Event
# from aware.communications.topics.topic import Topic
from aware.communication.primitives import Request
from aware.communication.protocols import (
    EventSubscriber,
    RequestClient,
    RequestService,
    TopicPublisher,
    TopicSubscriber,
)


class CommunicationProtocols:
    def __init__(
        self,
        topic_publishers: Dict[str, TopicPublisher],
        topic_subscribers: Dict[str, TopicSubscriber],
        request_clients: Dict[str, RequestClient],
        request_services: Dict[str, RequestService],
        event_subscribers: Dict[str, EventSubscriber],
    ):
        self.topic_publishers = topic_publishers
        self.topic_subscribers = topic_subscribers
        self.request_clients = request_clients
        self.request_services = request_services
        self.event_subscribers = event_subscribers

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
        return CommunicationProtocols(**data)

    def get_function_schemas(self) -> List[Dict[str, Any]]:
        # Add functions to create new request or publish new message.
        function_schemas: List[Dict[str, Any]] = []
        for publisher in self.topic_publishers.values():
            function_schemas.append(publisher.get_topic_as_function())
        for client in self.request_clients.values():
            function_schemas.append(client.get_request_as_function())

        # Add functions to set request as completed or send feedback.
        current_request = self.get_highest_prio_request()
        if current_request:
            for service in self.request_services.values():
                if current_request.service_id == service.service_id:
                    function_schemas.append(
                        service.get_set_request_completed_function()
                    )
                    if current_request.is_async():
                        function_schemas.append(service.get_send_feedback_function())
        return function_schemas

    def get_publisher_topic_id(self, topic_name: str) -> Optional[str]:
        publisher = self.topic_publishers.get(topic_name, None)
        if publisher is None:
            return None
        return publisher.topic_id

    def get_client(self, service_name: str) -> Optional[RequestClient]:
        return self.request_clients.get(service_name, None)

    def get_highest_prio_request(self) -> Optional[Request]:
        highest_prio_request = None
        for request_service in self.request_services.values():
            request = request_service.get_highest_prio_request()
            if request:
                if (
                    highest_prio_request is None
                    or request.data.priority > highest_prio_request.data.priority
                ):
                    highest_prio_request = request
        return highest_prio_request

    def to_prompt_kwargs(self):
        """Show permanent info on the prompt. Don't show event as it will be part of conversation."""
        prompt_kwargs = {}
        # Add the feedback of all the client requests
        requests_feedback = "\n".join(
            [
                clients.get_request_feedback()
                for clients in self.request_clients.values()
            ]
        )
        # TODO: Rename outgoing_requests to client_requests?
        prompt_kwargs.update({"outgoing_requests": requests_feedback})

        # TODO: Rename to service_request?
        incoming_request = self.get_highest_prio_request()
        if incoming_request:
            prompt_kwargs.update(
                {"incoming_request": incoming_request.query_to_string()}
            )

        # TODO: Get topics from topic_subscriber!
        topic_updates = "\n".join(
            [
                topic_subscriber.get_topic_update()
                for topic_subscriber in self.topic_subscribers.values()
            ]
        )
        prompt_kwargs.update({"topics": "\n".join(topic_updates)})
        return prompt_kwargs
