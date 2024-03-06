import json
from typing import Any, Dict, List, Optional

# from aware.communications.events.event import Event
# from aware.communications.topics.topic import Topic
from aware.communication.primitives import Request
from aware.communication.protocols import (
    EventSubscriber,
    TopicPublisher,
    TopicSubscriber,
    ActionClient,
    ActionService,
    # RequestClient,
    RequestService,
)
from aware.communication.protocols.request_client import RequestClient


class CommunicationProtocols:
    def __init__(
        self,
        event_subscribers: Dict[str, EventSubscriber],
        topic_publishers: Dict[str, TopicPublisher],
        topic_subscribers: Dict[str, TopicSubscriber],
        action_clients: Dict[str, ActionClient],
        action_services: Dict[str, ActionService],
        request_clients: Dict[str, RequestClient],
        request_services: Dict[str, RequestService],
    ):
        self.event_subscribers = event_subscribers
        self.topic_publishers = topic_publishers
        self.topic_subscribers = topic_subscribers
        self.action_clients = action_clients
        self.action_services = action_services
        self.request_clients = request_clients
        self.request_services = request_services

        self.service_request = self._get_highest_prio_request()

    def to_dict(self):
        return {
            "event_subscribers": {
                event_name: event_subscriber.to_dict()
                for event_name, event_subscriber in self.event_subscribers.items()
            },
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
            "action_services": {
                action_name: action_service.to_dict()
                for action_name, action_service in self.action_services.items()
            },
            "request_clients": {
                service_name: request_client.to_dict()
                for service_name, request_client in self.request_clients.items()
            },
            "request_services": {
                service_name: request_service.to_dict()
                for service_name, request_service in self.request_services.items()
            },
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str: str):
        data = json.loads(json_str)
        data["event_subscribers"] = {
            event_name: EventSubscriber(**event_subscriber)
            for event_name, event_subscriber in data["event_subscribers"].items()
        }
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
        data["action_services"] = {
            action_name: ActionService(**action_service)
            for action_name, action_service in data["action_services"].items()
        }
        data["request_clients"] = {
            request_name: RequestClient(**request_client)
            for request_name, request_client in data["request_clients"].items()
        }
        data["request_services"] = {
            request_name: RequestService(**request_service)
            for request_name, request_service in data["request_services"].items()
        }
        return CommunicationProtocols(**data)

    # TODO: Refactor -> For actions add set_action_completed and send_feedback, for request only set_request_completed.
    # The system should be processing only 1 at a time or an action or a request OR a event!!
    # TODO: With new refactor we have moved the logic to register functions to a common interface.
    # WE just need to add functions of all publishers/clients and the ones of the subscriber/service which handles the current input!
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

        # TODO: based on the input add the functions of the subscriber/service that is handling the input.

        # TODO: REMOVE. OLD ONE!!
        # Add topic_publisher functions
        for publisher in self.topic_publishers.values():
            function_schemas.append(publisher.get_topic_as_function())

        if self.service_request:
            # Add request_service functions TODO: Get service using request_name, but request doesn't have name.. refactor it.
            for service in self.request_services.values():
                if self.service_request.service_id == service.service_id:
                    function_schemas.append(
                        service.get_set_request_completed_function()
                    )
                    if self.service_request.is_async():
                        function_schemas.append(service.get_send_feedback_function())
        return function_schemas

    def call_function(
        self, function_name: str, function_args: Dict[str, Any]
    ) -> Optional[str]:
        # TODO: make this more elegant.
        for publisher in self.topic_publishers.values():
            if function_name == publisher.function_exists(function_name):
                return publisher.call_function(function_name, function_args)
        for client in self.request_clients.values():
            if function_name == client.function_exists(function_name):
                return client.call_function(function_name, function_args)
        for client in self.action_clients.values():
            if function_name == client.function_exists(function_name):
                return client.call_function(function_name, function_args)
        # TODO: Get the protocol that is providing the request and repeat the pattern to call the function in case it exists.
        return None

    def get_publisher(self, topic_name: str) -> Optional[TopicPublisher]:
        return self.topic_publishers.get(topic_name, None)

    def get_client(self, service_name: str) -> Optional[RequestClient]:
        return self.request_clients.get(service_name, None)

    def get_service(self, service_name: str) -> Optional[RequestService]:
        return self.request_services.get(service_name, None)

    # TODO: refactor this, we should determine if highest prio is request/action or event and use it at prompt.
    def _get_highest_prio_request(self) -> Optional[Request]:
        highest_prio_request = None
        for request_service in self.request_services.values():
            request = request_service.current_request
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
        # Add the feedback of all the client actions
        actions_feedback = "\n".join(
            [clients.get_action_feedback() for clients in self.action_clients.values()]
        )
        # TODO: Rename at meta-prompt.
        prompt_kwargs.update({"actions_feedback": actions_feedback})

        # TODO: Determine if it should be a request/action or event.
        if self.service_request:
            prompt_kwargs.update(
                {"incoming_request": self.service_request.query_to_string()}
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
