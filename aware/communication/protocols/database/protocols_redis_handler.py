from redis import Redis
from typing import Optional

from aware.communication.protocols import (
    EventSubscriber,
    EventPublisher,
    RequestClient,
    RequestService,
    TopicPublisher,
    TopicSubscriber,
)
from aware.communication.primitives.event import Event
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
        # TODO: verify if needed
        self.client.set(
            f"topic_publisher:{topic_publisher.id}:topic",
            topic_publisher.topic_id,
        )

    def create_topic_subscriber(self, topic_subscriber: TopicSubscriber):
        self.client.sadd(
            f"process:{topic_subscriber.process_id}:topic_subscribers",
            topic_subscriber.to_json(),
        )
        # TODO: verify if needed
        self.client.set(
            f"topic_subscriber:{topic_subscriber.id}:topic",
            topic_subscriber.topic_id,
        )

    def get_communication_protocols(self, process_id: str) -> CommunicationProtocols:
        return CommunicationProtocols(
            topic_publisher=self.get_topic_publisher(process_id=process_id),
            topic_subscriber=self.get_topic_subscriber(process_id=process_id),
            request_client=self.get_request_client(process_id=process_id),
            request_service=self.get_request_service(service_id=process_id),
            event_subscriber=self.get_event_subscriber(process_id=process_id),
        )

    def get_event_subscriber(self, process_id: str) -> EventSubscriber:
        data = self.client.get(f"process:{process_id}:event_subscribers")
        if data:
            return EventSubscriber.from_json(data)
        return None

    # TODO: event_publisher doesn't depend on any process. It should be external.
    def get_event_publisher(self, process_id: str) -> EventPublisher:
        data = self.client.get(f"process:{process_id}:event_publisher")
        if data:
            return EventPublisher.from_json(data)
        return None

    def get_request_client(
        self,
        process_id: str,
    ) -> Optional[RequestService]:
        data = self.client.get(f"process:{process_id}:request_client")
        if data:
            return RequestClient.from_json(data)
        return None

    def get_request_service(
        self,
        process_id: str,
    ) -> Optional[RequestService]:
        data = self.client.get(f"process:{process_id}:request_service")
        if data:
            return RequestService.from_json(data)
        return None

    def get_topic_publisher(self, process_id: str) -> TopicSubscriber:
        data = self.client.get(f"process:{process_id}:topic_publisher")
        if data:
            return TopicPublisher.from_json(data)
        return None

    def get_topic_subscriber(self, process_id: str) -> TopicSubscriber:
        data = self.client.get(f"process:{process_id}:topic_subscribers")
        if data:
            return TopicSubscriber.from_json(data)
        return None

    def set_communications(
        self, process_id: str, communication_protocols: CommunicationProtocols
    ):
        for topic_publisher in communication_protocols.topic_publishers:
            self.create_topic_publisher(topic_publisher)
        for topic_subscriber in communication_protocols.topic_subscribers:
            self.create_topic_subscriber(process_id, topic_subscriber)
        for request_client in communication_protocols.request_clients:
            self.create_request_client(process_id, request_client)
        for request_service in communication_protocols.request_services:
            self.create_request_service(process_id, request_service)
        for event_subscriber in communication_protocols.event_subscribers:
            self.create_event_subscriber(process_id, event_subscriber)
