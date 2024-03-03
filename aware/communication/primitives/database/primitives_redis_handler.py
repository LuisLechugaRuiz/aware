from redis import Redis
from typing import Optional

from aware.communication.primitives.event import Event, EventType
from aware.communication.primitives.request import Request
from aware.communication.primitives.topic import Topic
from aware.utils.logger.file_logger import FileLogger
from aware.utils.helpers import convert_timestamp_to_epoch, get_current_date_iso8601


class PrimitivesRedisHandler:
    def __init__(self, client: Redis):
        self.client = client

    def create_event(self, event: Event):
        # Convert the event to JSON and store it
        self.client.set(f"event:{event.id}", event.to_json())
        # Order the events by timestamp
        event_order_key = f"event_types:{event.event_type_id}:events:order"
        self.client.zadd(
            event_order_key,
            {event.id: convert_timestamp_to_epoch(event.timestamp)},
        )

    def create_event_type(self, event_type: EventType):
        event_type_key = f"event_type:{event_type.id}"
        self.client.set(event_type_key, event_type.to_json())

    def create_request(self, request: Request):
        # Key for storing the serialized request
        request_data_key = f"request:{request.id}"

        # Key for the sorted set to maintain the order of requests by timestamp
        request_service_order_key = (
            f"request_service:{request.service_id}:requests:order"
        )

        # Convert the request to JSON and store it
        self.client.set(request_data_key, request.to_json())

        # Add the request ID to the service process sorted set with the timestamp as the score
        timestamp = convert_timestamp_to_epoch(request.timestamp)
        self.client.zadd(
            request_service_order_key,
            {request.id: timestamp},
        )

        # Add the request ID to the client process sorted set if the request is async
        if request.is_async():
            request_client_order_key = (
                f"request_client:{request.client_id}:requests:order"
            )
            self.client.zadd(
                request_client_order_key,
                {request.id: timestamp},
            )

    def create_topic(self, topic: Topic):
        self.client.set(
            f"topic:{topic.id}",
            topic.to_json(),
        )

    def get_client_requests(self, client_id: str):
        return self.get_requests(f"request_client:{client_id}:requests:order")

    def get_service_requests(self, service_id: str):
        return self.get_requests(f"request_service:{service_id}:requests:order")

    def get_requests(self, request_order_key: str):
        # Retrieve all request IDs from the sorted set, ordered by timestamp
        request_ids = self.client.zrange(request_order_key, 0, -1)

        requests = []
        for request_id_bytes in request_ids:
            request_id = request_id_bytes.decode("utf-8")

            # Fetch the request data for each request ID and deserialize it
            request_data_json = self.client.get(f"request:{request_id}")
            if request_data_json:
                requests.append(Request.from_json(request_data_json.decode("utf-8")))

        return requests

    def get_topic(self, topic_id: str) -> Optional[Topic]:
        data = self.client.get(f"topic:{topic_id}")
        if data:
            return Topic.from_json(data)
        return None
