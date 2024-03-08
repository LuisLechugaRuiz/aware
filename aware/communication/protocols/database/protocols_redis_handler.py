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
        self.client.sadd(
            f"event_type:{event_subscriber.event_type_id}:event_subscribers",
            event_subscriber.to_json(),
        )
        self.client.set(
            f"event_subscriber:{event_subscriber.id}",
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
        self.client.set(
            f"event_publisher:{event_publisher.id}",
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
        self.client.set(
            f"action_client:{action_client.id}",
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
        self.client.set(
            f"action_service:{action_service.id}",
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
        self.client.set(
            f"request_client:{request_client.id}",
            request_client.to_json(),
        )

    def create_request_service(self, request_service: RequestService):
        self.client.sadd(
            f"process:{request_service.process_id}:request_service",
            request_service.to_json(),
        )
        self.client.set(
            f"request_service:{request_service.id}",
            request_service.to_json(),
        )

    def create_topic_publisher(self, topic_publisher: TopicPublisher):
        self.client.sadd(
            f"process:{topic_publisher.process_id}:topic_publishers",
            topic_publisher.to_json(),
        )
        self.client.set(
            f"topic_publisher:{topic_publisher.id}",
            topic_publisher.to_json(),
        )

    def create_topic_subscriber(self, topic_subscriber: TopicSubscriber):
        self.client.sadd(
            f"process:{topic_subscriber.process_id}:topic_subscribers",
            topic_subscriber.to_json(),
        )
        self.client.set(
            f"topic_subscriber:{topic_subscriber.id}",
            topic_subscriber.to_json(),
        )
        self.client.sadd(
            f"topic:{topic_subscriber.topic_id}:subscribers",
            topic_subscriber.to_json(),
        )

    def get_event_subscribers_from_type(
        self, event_type_id: str
    ) -> Dict[str, EventSubscriber]:
        event_subscribers = {}
        for event_subscriber in self.client.smembers(
            f"event_type:{event_type_id}:event_subscribers"
        ):
            event_subscriber = EventSubscriber.from_json(event_subscriber)
            event_subscribers[event_subscriber.process_id] = event_subscriber
        return event_subscribers

    def get_event_subscriber(
        self, event_subscriber_id: str
    ) -> Optional[EventSubscriber]:
        data = self.client.get(f"event_subscriber:{event_subscriber_id}")
        if data:
            return EventSubscriber.from_json(data)
        return None

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

    def get_action_client(self, action_client_id: str) -> Optional[ActionClient]:
        data = self.client.get(f"action_client:{action_client_id}")
        if data:
            return ActionClient.from_json(data)
        return None

    def get_action_clients(self, process_id: str) -> Dict[str, ActionClient]:
        action_clients = {}
        for action_client in self.client.smembers(
            f"process:{process_id}:action_clients"
        ):
            action_client = ActionClient.from_json(action_client)
            action_clients[action_client.service_name] = action_client
        return action_clients

    def get_action_service(self, action_service_id: str) -> Optional[ActionService]:
        data = self.client.get(f"action_service:{action_service_id}")
        if data:
            return ActionService.from_json(data)
        return None

    def get_action_services(self, process_id: str) -> Dict[str, ActionService]:
        action_services = {}
        for action_service in self.client.smembers(
            f"process:{process_id}:action_services"
        ):
            action_service = ActionService.from_json(action_service)
            action_services[action_service.service_name] = action_service
        return action_services

    def get_request_client(self, request_client_id: str) -> Optional[RequestClient]:
        data = self.client.get(f"request_client:{request_client_id}")
        if data:
            return RequestClient.from_json(data)
        return None

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

    def get_request_service(self, request_service_id: str) -> Optional[RequestService]:
        data = self.client.get(f"request_service:{request_service_id}")
        if data:
            return RequestService.from_json(data)
        return None

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

    def get_topic_publisher(self, topic_publisher_id: str) -> Optional[TopicPublisher]:
        data = self.client.get(f"topic_publisher:{topic_publisher_id}")
        if data:
            return TopicPublisher.from_json(data)
        return None

    def get_topic_publishers(self, process_id: str) -> Dict[str, TopicPublisher]:
        topic_publishers = {}
        for topic_publisher in self.client.smembers(
            f"process:{process_id}:topic_publishers"
        ):
            topic_publisher = TopicPublisher.from_json(topic_publisher)
            topic_publishers[topic_publisher.topic_name] = topic_publisher
        return topic_publishers

    def get_topic_subscriber(
        self, topic_subscriber_id: str
    ) -> Optional[TopicSubscriber]:
        data = self.client.get(f"topic_subscriber:{topic_subscriber_id}")
        if data:
            return TopicSubscriber.from_json(data)
        return None

    def get_topic_subscribers(self, process_id: str) -> Dict[str, TopicSubscriber]:
        topic_subscribers = {}
        for topic_subscriber in self.client.smembers(
            f"process:{process_id}:topic_subscribers"
        ):
            topic_subscriber = TopicSubscriber.from_json(topic_subscriber)
            topic_subscribers[topic_subscriber.topic_name] = topic_subscriber
        return topic_subscribers

    def get_topic_subscribers_from_topic(
        self, topic_id: str
    ) -> Dict[str, TopicSubscriber]:
        topic_subscribers = {}
        for topic_subscriber in self.client.smembers(f"topic:{topic_id}:subscribers"):
            topic_subscriber = TopicSubscriber.from_json(topic_subscriber)
            topic_subscribers[topic_subscriber.process_id] = topic_subscriber
        return topic_subscribers
