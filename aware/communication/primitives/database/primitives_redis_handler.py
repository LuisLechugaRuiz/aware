from redis import Redis
from typing import Any, Dict, Optional

from aware.communication.primitives.action import Action
from aware.communication.primitives.event import Event, EventType
from aware.communication.primitives.request import Request
from aware.communication.primitives.topic import Topic
from aware.utils.helpers import convert_timestamp_to_epoch, get_current_date_iso8601


# TODO: Refactor, add actions and remove async requests.
class PrimitivesRedisHandler:
    def __init__(self, client: Redis):
        self.client = client

    def create_action(self, action: Action):
        # Convert the action to JSON and store it
        self.client.set(f"action:{action.id}", action.to_json())
        # Order the actions by priority
        service_order_key = f"action_service:{action.service_id}:actions:order"
        self.client.zadd(
            service_order_key,
            {action.id: action.data.priority},
        )
        client_order_key = f"action_client:{action.client_id}:actions:order"
        self.client.zadd(
            client_order_key,
            {action.id: action.data.priority},
        )

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

    # TODO: IMPLEMENT ME!
    # def create_request_type(self, request_type: RequestType):

    def create_request(self, request: Request):
        # Convert the request to JSON and store it
        self.client.set(f"request:{request.id}", request.to_json())

        # Key for the sorted set to maintain the order of requests by timestamp
        self.client.zadd(
            f"request_service:{request.service_id}:requests:order",
            {request.id: request.data.priority},
        )
        self.client.zadd(
            f"request_client:{request.client_id}:requests:order",
            {request.id: request.data.priority},
        )

    def create_topic(self, topic: Topic):
        self.client.set(
            f"topic:{topic.id}",
            topic.to_json(),
        )

    # TODO: REFACTOR!
    def delete_event(self, event: Event):
        # Delete the event data
        event_data_key = (
            f"user_id:{event.user_id}:event_type:{event.event_name}:event:{event.id}"
        )
        self.client.delete(event_data_key)

        # Delete the event reference from the sorted set
        event_order_key = (
            f"user_id:{event.user_id}:event_type:{event.event_name}:event:order"
        )
        self.client.zrem(event_order_key, event_data_key)

    def delete_request(self, request: Request):
        self.client.delete(f"request:{request.id}")

        self.client.zrem(
            f"request_service:{request.service_id}:requests:order",
            request.id,
        )
        self.client.zrem(f"request_client:{request.client_id}:requests:order")

    def get_client_actions(self, action_id: str):
        return self.get_actions(f"action_client:{action_id}:actions:order")

    def get_service_actions(self, action_id: str):
        return self.get_actions(f"action_service:{action_id}:actions:order")

    def get_client_requests(self, client_id: str):
        return self.get_requests(f"request_client:{client_id}:requests:order")

    def get_service_requests(self, service_id: str):
        return self.get_requests(f"request_service:{service_id}:requests:order")

    def get_actions(self, action_order_key: str):
        action_ids = self.client.zrange(action_order_key, 0, -1)

        actions = []
        for action_id_bytes in action_ids:
            action_id = action_id_bytes.decode("utf-8")

            action_data_json = self.client.get(f"action:{action_id}")
            if action_data_json:
                actions.append(Action.from_json(action_data_json.decode("utf-8")))

        return actions

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

    def update_action(self, action: Action):
        self.client.set(f"action:{action.id}", action.to_json())

    def update_topic(self, topic_id: str, message: Dict[str, Any]):
        topic = self.get_topic(topic_id)
        topic.message = message
        topic.timestamp = get_current_date_iso8601()

        self.client.set(
            f"topic:{topic_id}",
            topic.to_json(),
        )

    def update_request(self, request: Request):
        self.client.set(f"request:{request.id}", request.to_json())
