from redis import Redis
from typing import Any, Dict, List, Optional

from aware.communication.helpers.current_input_metadata import CurrentInputMetadata
from aware.communication.primitives.action import Action
from aware.communication.primitives.event import Event, EventType
from aware.communication.primitives.request import Request
from aware.communication.primitives.topic import Topic
from aware.utils.helpers import convert_timestamp_to_epoch, get_current_date_iso8601


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

    def delete_current_input_metadata(self, process_id: str):
        self.client.delete(f"current_input:{process_id}")

    def delete_action(self, action: Action):
        self.client.delete(f"action:{action.id}")

        self.client.zrem(
            f"action_service:{action.service_id}:actions:order",
            action.id,
        )
        self.client.zrem(
            f"action_client:{action.client_id}:actions:order",
            action.id,
        )

    def delete_event(self, event: Event):
        self.client.delete(f"event:{event.id}")
        self.client.zrem(
            f"event_types:{event.event_type_id}:events:order",
            event.id,
        )

    def delete_request(self, request: Request):
        self.client.delete(f"request:{request.id}")

        self.client.zrem(
            f"request_service:{request.service_id}:requests:order",
            request.id,
        )
        self.client.zrem(f"request_client:{request.client_id}:requests:order")

    def get_current_input_metadata(
        self, process_id: str
    ) -> Optional[CurrentInputMetadata]:
        metadata = self.client.get(f"current_input:{process_id}")
        if metadata:
            return CurrentInputMetadata.from_json(metadata)
        return None

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

            action = self.get_action(action_id)
            if action is not None:
                actions.append(action)

        return actions

    # TODO: Fix me?
    def get_events(self, event_type_id: str) -> List[Event]:
        # Retrieve all event IDs from the sorted set, ordered by timestamp
        events_order_key = f"event_types:{event_type_id}:events:order"
        events_ids = self.client.zrange(events_order_key, 0, -1)

        events = []
        for event_id_bytes in events_ids:
            event_id = event_id_bytes.decode("utf-8")

            # Fetch the event data for each event ID and deserialize it
            event = self.get_event(event_id)
            if event is not None:
                events.append(event)

        return events

    def get_requests(self, request_order_key: str):
        # Retrieve all request IDs from the sorted set, ordered by timestamp
        request_ids = self.client.zrange(request_order_key, 0, -1)

        requests = []
        for request_id_bytes in request_ids:
            request_id = request_id_bytes.decode("utf-8")

            # Fetch the request data for each request ID and deserialize it
            request = self.get_request(request_id)
            if request is not None:
                requests.append(request)

        return requests

    def get_action(self, action_id: str) -> Optional[Action]:
        data = self.client.get(f"action:{action_id}")
        if data:
            return Action.from_json(data)
        return None

    def get_event(self, event_id: str) -> Optional[Event]:
        data = self.client.get(f"event:{event_id}")
        if data:
            return Event.from_json(data)
        return None

    def get_request(self, request_id: str) -> Optional[Request]:
        data = self.client.get(f"request:{request_id}")
        if data:
            return Request.from_json(data)
        return None

    def get_topic(self, topic_id: str) -> Optional[Topic]:
        data = self.client.get(f"topic:{topic_id}")
        if data:
            return Topic.from_json(data)
        return None

    def set_current_input_metadata(
        self, process_id: str, current_input_metadata: CurrentInputMetadata
    ):
        self.client.set(
            f"current_input:{process_id}",
            current_input_metadata.to_json(),
        )

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
