from redis import Redis
from typing import Dict, Optional

from aware.communication.protocols import (
    EventSubscriber,
    EventPublisher,
    TopicPublisher,
    TopicSubscriber,
    RequestClient,
    RequestService,
    ActionClient,
    ActionService,
)
from aware.communication.communication_protocols import CommunicationProtocols


class ProtocolsRedisHandler:
    def __init__(self, client: Redis):
        self.client = client

    def create_event_subscriber(
        self,
        event_subscriber: EventSubscriber,
    ):
        self.client.sadd(
            f"process:{event_subscriber.process_id}:event_subscribers",
            event_subscriber.to_json(),
        )

    def create_event_publisher(
        self,
        event_publisher: EventPublisher,
    ):
        self.client.sadd(
            f"process:{event_publisher.process_id}:event_publishers",
            event_publisher.to_json(),
        )

    def create_action_client(
        self,
        action_client: ActionClient,
    ):
        self.client.sadd(
            f"process:{action_client.process_id}:action_clients",
            action_client.to_json(),
        )

    def create_action_service(
        self,
        action_service: ActionService,
    ):
        self.client.sadd(
            f"process:{action_service.process_id}:action_services",
            action_service.to_json(),
        )

    def create_request_client(
        self,
        request_client: RequestClient,
    ):
        self.client.sadd(
            f"process:{request_client.process_id}:request_clients",
            request_client.to_json(),
        )

    def create_request_service(self, request_service: RequestService):
        self.client.sadd(
            f"process:{request_service.process_id}:request_service",
            request_service.to_json(),
        )

    def create_topic_publisher(self, topic_publisher: TopicPublisher):
        self.client.sadd(
            f"process:{topic_publisher.process_id}:topic_publishers",
            topic_publisher.to_json(),
        )

    def create_topic_subscriber(self, topic_subscriber: TopicSubscriber):
        self.client.sadd(
            f"process:{topic_subscriber.process_id}:topic_subscribers",
            topic_subscriber.to_json(),
        )

    def get_communication_protocols(self, process_id: str) -> CommunicationProtocols:
        return CommunicationProtocols(
            event_subscribers=self.get_event_subscribers(process_id=process_id),
            topic_publishers=self.get_topic_publishers(process_id=process_id),
            topic_subscribers=self.get_topic_subscribers(process_id=process_id),
            action_clients=self.get_action_clients(process_id=process_id),
            action_services=self.get_action_services(process_id=process_id),
            request_clients=self.get_request_clients(process_id=process_id),
            request_service=self.get_request_services(service_id=process_id),
        )

    def get_event_subscribers(self, process_id: str) -> Dict[str, EventSubscriber]:
        event_subscribers = {}
        for event_subscriber in self.client.smembers(
            f"process:{process_id}:event_subscribers"
        ):
            event_subscriber = EventSubscriber.from_json(event_subscriber)
            event_subscribers[event_subscriber.event_name] = event_subscriber
        return event_subscribers

    # TODO: event_publisher doesn't depend on any process. It should be external!!
    # def get_event_publishers(self, process_id: str) -> EventPublisher:
    #     data = self.client.get(f"process:{process_id}:event_publisher")
    #     if data:
    #         return EventPublisher.from_json(data)
    #     return None

    def get_action_clients(self, process_id: str) -> Dict[str, ActionClient]:
        action_clients = {}
        for action_client in self.client.smembers(
            f"process:{process_id}:action_clients"
        ):
            action_client = ActionClient.from_json(action_client)
            action_clients[action_client.service_name] = action_client
        return action_clients

    def get_action_services(self, process_id: str) -> Dict[str, ActionService]:
        action_services = {}
        for action_service in self.client.smembers(
            f"process:{process_id}:action_services"
        ):
            action_service = ActionService.from_json(action_service)
            action_services[action_service.service_name] = action_service
        return action_services

    def get_request_clients(
        self,
        process_id: str,
    ) -> Dict[str, RequestClient]:
        request_clients = {}
        for request_client in self.client.smembers(
            f"process:{process_id}:request_clients"
        ):
            request_client = RequestClient.from_json(request_client)
            request_clients[request_client.service_name] = request_client
        return request_clients

    def get_request_services(
        self,
        process_id: str,
    ) -> Dict[str, RequestService]:
        request_services = {}
        for request_service in self.client.smembers(
            f"process:{process_id}:request_service"
        ):
            request_service = RequestService.from_json(request_service)
            request_services[request_service.data.service_name] = request_service
        return request_services

    def get_topic_publishers(self, process_id: str) -> Dict[str, TopicPublisher]:
        topic_publishers = {}
        for topic_publisher in self.client.smembers(
            f"process:{process_id}:topic_publishers"
        ):
            topic_publisher = TopicPublisher.from_json(topic_publisher)
            topic_publishers[topic_publisher.topic_name] = topic_publisher
        return topic_publishers

    def get_topic_subscribers(self, process_id: str) -> Dict[str, TopicSubscriber]:
        topic_subscribers = {}
        for topic_subscriber in self.client.smembers(
            f"process:{process_id}:topic_subscribers"
        ):
            topic_subscriber = TopicSubscriber.from_json(topic_subscriber)
            topic_subscribers[topic_subscriber.topic_name] = topic_subscriber
        return topic_subscribers

    def set_communications(
        self, process_id: str, communication_protocols: CommunicationProtocols
    ):
        for event_subscriber in communication_protocols.event_subscribers:
            self.create_event_subscriber(process_id, event_subscriber)
        for topic_publisher in communication_protocols.topic_publishers:
            self.create_topic_publisher(topic_publisher)
        for topic_subscriber in communication_protocols.topic_subscribers:
            self.create_topic_subscriber(process_id, topic_subscriber)
        for action_client in communication_protocols.action_clients:
            self.create_action_client(process_id, action_client)
        for action_service in communication_protocols.action_services:
            self.create_action_service(process_id, action_service)
        for request_client in communication_protocols.request_clients:
            self.create_request_client(process_id, request_client)
        for request_service in communication_protocols.request_services:
            self.create_request_service(process_id, request_service)
