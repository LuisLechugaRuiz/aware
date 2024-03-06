import json
from typing import Any, Dict, List, Optional

from aware.communication.protocols import (
    EventSubscriber,
    TopicPublisher,
    TopicSubscriber,
    ActionClient,
    ActionService,
    RequestClient,
    RequestService,
)


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

        self._get_highest_prio_input()

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

    def get_service(self, service_name: str) -> Optional[RequestService]:
        return self.request_services.get(service_name, None)

    # TODO: refactor this, make it cleaner.
    def _get_highest_prio_input(self):
        self.highest_prio_input = None
        self.input_protocol = None
        for request_service in self.request_services.values():
            requests = request_service.get_requests()
            for request in requests:
                if request:
                    if (
                        self.highest_prio_input is None
                        or request.priority > self.highest_prio_input.priority
                    ):
                        self.highest_prio_input = request
                        self.input_protocol = request_service
        for action_service in self.action_services.values():
            actions = action_service.get_actions()
            for action in actions:
                if action:
                    if (
                        self.highest_prio_input is None
                        or action.priority > self.highest_prio_input.priority
                    ):
                        self.highest_prio_input = action
                        self.input_protocol = action_service
        for event_subscriber in self.event_subscribers.values():
            events = event_subscriber.get_events()
            for event in events:
                if event:
                    if (
                        self.highest_prio_input is None
                        or event.priority > self.highest_prio_input.priority
                    ):
                        self.highest_prio_input = event
                        self.input_protocol = event_subscriber

    def to_prompt_kwargs(self):
        """Show permanent info on the prompt. Don't show event as it will be part of conversation."""
        prompt_kwargs = {}

        # Add the input
        if self.highest_prio_input:
            prompt_kwargs.update(
                {"input": self.highest_prio_input.input_to_prompt_string()}
            )

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
