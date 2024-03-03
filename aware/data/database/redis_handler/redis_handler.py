import json
from redis import Redis
from typing import Any, Dict, List, Optional, Tuple

from aware.agent.agent_data import AgentData
from aware.memory.user.user_data import UserData
from aware.chat.conversation_schemas import (
    ChatMessage,
    JSONMessage,
    UserMessage,
    AssistantMessage,
    SystemMessage,
    ToolResponseMessage,
    ToolCalls,
)
from aware.chat.call_info import CallInfo
from aware.communication.communication_protocols import Communications
from aware.communication.events.event import Event
from aware.communication.events.event_subscriber import EventSubscriber
from aware.communication.events.event_publisher import EventPublisher
from aware.communication.events.event_type import EventType
from aware.communication.requests.request import Request
from aware.communication.requests.request_client import RequestClient
from aware.communication.requests.request_service import RequestService
from aware.communication.topics.topic import Topic
from aware.communication.topics.topic_subscriber import TopicSubscriber
from aware.communication.topics.topic_publisher import TopicPublisher
from aware.process.process_data import ProcessData
from aware.process.process_ids import ProcessIds
from aware.process.state_machine.state import ProcessState
from aware.utils.helpers import convert_timestamp_to_epoch, get_current_date_iso8601


class RedisHandler:
    def __init__(self, client: Redis):
        self.client = client

    def add_call_info(self, call_info: CallInfo):
        self.client.set(
            f"call_info:{call_info.call_id}",
            call_info.to_json(),
        )
        self.client.lpush("pending_call", call_info.call_id)

    def add_message(
        self,
        process_id: str,
        chat_message: ChatMessage,
    ):
        message = chat_message.message
        key = f"conversation:{process_id}:message:{chat_message.message_id}"
        message_data = json.dumps(
            {"type": type(message).__name__, "data": message.to_json()}
        )
        self.client.hmset(key, {"data": message_data})

        # Add the key to the sorted set with timestamp as the score
        conversation_key = f"conversation:{process_id}"
        self.client.zadd(
            conversation_key, {key: convert_timestamp_to_epoch(chat_message.timestamp)}
        )
        self.add_message_to_buffer(process_id, chat_message)

    def add_message_to_buffer(
        self,
        process_id: str,
        chat_message: ChatMessage,
    ):
        message = chat_message.message
        key = f"conversation_buffer:{process_id}:message:{chat_message.message_id}"
        message_data = json.dumps(
            {"type": type(message).__name__, "data": message.to_json()}
        )
        self.client.hmset(key, {"data": message_data})
        conversation_buffer_key = f"conversation_buffer:{process_id}"
        self.client.zadd(
            conversation_buffer_key,
            {key: convert_timestamp_to_epoch(chat_message.timestamp)},
        )

    def add_active_agent(self, agent_id: str):
        self.client.sadd("active_agents", agent_id)

    def clear_conversation_buffer(self, process_id: str):
        self.client.delete(f"conversation_buffer:{process_id}")

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

    def create_process_state(self, process_id: str, process_state: ProcessState):
        self.client.sadd(
            f"process:{process_id}:states",
            process_state.to_json(),
        )

    def create_topic(self, topic: Topic):
        self.client.set(
            f"topic:{topic.id}",
            topic.to_json(),
        )

    def create_topic_publisher(self, topic_publisher: TopicPublisher):
        self.client.sadd(
            f"process:{topic_publisher.process_id}:topic_publishers",
            topic_publisher.to_json(),
        )
        self.client.set(
            f"topic_publisher:{topic_publisher.id}:topic",
            topic_publisher.topic_id,
        )

    def create_topic_subscriber(self, topic_subscriber: TopicSubscriber):
        self.client.sadd(
            f"process:{topic_subscriber.process_id}:topic_subscribers",
            topic_subscriber.to_json(),
        )
        self.client.set(
            f"topic_subscriber:{topic_subscriber.id}:topic",
            topic_subscriber.topic_id,
        )

    def create_request_client(self, request_client: RequestClient):
        self.client.sadd(
            f"process:{request_client.process_id}:request_client",
            request_client.to_json(),
        )

    def create_request_service(self, request_service: RequestService):
        self.client.sadd(
            f"process:{request_service.process_id}:request_service",
            request_service.to_json(),
        )

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

    def delete_event(self, event: Event):
        # Delete the event data
        event_data_key = (
            f"user_id:{event.user_id}:event_type:{event.name}:event:{event.id}"
        )
        self.client.delete(event_data_key)

        # Delete the event reference from the sorted set
        event_order_key = f"user_id:{event.user_id}:event_type:{event.name}:event:order"
        self.client.zrem(event_order_key, event_data_key)

    def delete_message(self, process_id: str, message_id: str):
        # The key for the specific message
        message_key = f"conversation:{process_id}:message:{message_id}"

        # Remove the hash storing the message details
        self.client.delete(message_key)

        # Remove the message reference from the sorted set
        conversation_key = f"conversation:{process_id}"
        self.client.zrem(conversation_key, message_key)

    def delete_request(self, request: Request):
        self.client.delete(f"request:{request.id}")

        self.client.zrem(
            f"request_service:{request.service_id}:requests:order",
            request.id,
        )
        if request.is_async():
            self.client.zrem(f"request_client:{request.client_id}:requests:order")

    def get_agent_data(self, agent_id: str) -> Optional[AgentData]:
        data = self.client.get(f"agent:{agent_id}")
        if data:
            return AgentData.from_json(data)
        return None

    def get_agent_id_by_process_id(self, process_id: str) -> str:
        agent_id = self.client.get(f"process:{process_id}:agent_id")
        if agent_id:
            return agent_id.decode()
        else:
            return None

    def get_agent_process_id(self, agent_id: str, process_name: str) -> Optional[str]:
        process_id = self.client.get(f"agent:{agent_id}:process_name:{process_name}")
        if process_id:
            return process_id.decode()
        return None

    def get_conversation(self, process_id: str) -> List[JSONMessage]:
        conversation_key = f"conversation:{process_id}"

        # Retrieve all message keys from the sorted set, ordered by timestamp
        message_keys = self.client.zrange(conversation_key, 0, -1)

        messages = []
        for message_key in message_keys:
            message_data = self.client.hget(message_key, "data")
            if message_data:
                message_data_str = message_data.decode()
                message = self.reconstruct_message(message_data_str)
                messages.append(message)

        return messages

    def get_conversation_with_keys(
        self, process_id: str
    ) -> List[Tuple[str, JSONMessage]]:
        conversation_key = f"conversation:{process_id}"
        message_keys = self.client.zrange(conversation_key, 0, -1)

        messages_with_keys = []
        for message_key in message_keys:
            message_data = self.client.hget(message_key, "data")
            if message_data:
                message_data_str = message_data.decode()
                message = self.reconstruct_message(message_data_str)
                messages_with_keys.append((message_key, message))

        return messages_with_keys

    def get_conversation_buffer(self, process_id: str) -> List[JSONMessage]:
        conversation_key = f"conversation_buffer:{process_id}"

        # Retrieve all message keys from the sorted set, ordered by timestamp
        message_keys = self.client.zrange(conversation_key, 0, -1)

        messages = []
        for message_key in message_keys:
            message_data = self.client.hget(message_key, "data")
            if message_data:
                message_data_str = message_data.decode()
                message = self.reconstruct_message(message_data_str)
                messages.append(message)

        return messages

    def get_current_process_state(self, process_id: str) -> Optional[ProcessState]:
        data = self.client.get(f"process:{process_id}:current_state")
        if data:
            return ProcessState.from_json(data)
        return None

    def get_events(self, event_type_id: str) -> List[Event]:
        # Retrieve all event IDs from the sorted set, ordered by timestamp
        events_order_key = f"event_types:{event_type_id}:events:order"
        events_ids = self.client.zrange(events_order_key, 0, -1)

        events = []
        for event_id_bytes in events_ids:
            event_id = event_id_bytes.decode("utf-8")

            # Fetch the event data for each event ID and deserialize it
            event_data_json = self.client.get(f"event:{event_id}")
            if event_data_json:
                events.append(Event.from_json(event_data_json.decode("utf-8")))

        return events

    def get_event_subscriber(self, process_id: str) -> EventSubscriber:
        data = self.client.get(f"process:{process_id}:event_subscribers")
        if data:
            event_subscriber = EventSubscriber.from_json(data)
            events = self.get_events(event_type_id=event_subscriber.event_type_id)
            event_subscriber.add_events(events)
            return event_subscriber
        return None

    def get_communications(self, process_id: str) -> Communications:
        return Communications(
            topic_publisher=self.get_topic_publisher(process_id=process_id),
            topic_subscriber=self.get_topic_subscriber(process_id=process_id),
            request_client=self.get_request_client(process_id=process_id),
            request_service=self.get_request_service(service_id=process_id),
            event_subscriber=self.get_event_subscriber(process_id=process_id),
        )

    def get_process_data(self, process_id: str) -> Optional[ProcessData]:
        data = self.client.get(f"process_data:{process_id}")
        if data:
            return ProcessData.from_json(data)
        return None

    def get_process_ids(self, process_id: str) -> Optional[ProcessIds]:
        data = self.client.get(f"process_ids:{process_id}")
        if data:
            return ProcessIds.from_json(data)
        return None

    def get_process_states(self, process_id: str) -> List[ProcessState]:
        process_states = self.client.smembers(f"process:{process_id}:states")
        return [
            ProcessState.from_json(process_state) for process_state in process_states
        ]

    def get_topic(self, topic_id: str) -> Optional[Topic]:
        data = self.client.get(f"topic:{topic_id}")
        if data:
            return Topic.from_json(data)
        return None

    def get_topic_publisher(self, process_id: str) -> TopicSubscriber:
        data = self.client.get(f"process:{process_id}:topic_publisher")
        if data:
            topic_publisher = TopicPublisher.from_json(data)
            topic_id = self.client.get(f"topic_publisher:{topic_publisher.id}:topic")
            topic = self.get_topic(topic_id)
            topic_publisher.add_topic(topic)
            return topic_publisher
        return None

    def get_topic_subscriber(self, process_id: str) -> TopicSubscriber:
        data = self.client.get(f"process:{process_id}:topic_subscribers")
        if data:
            topic_subscriber = TopicSubscriber.from_json(data)
            topic_id = self.client.get(f"topic_subscriber:{topic_subscriber.id}:topic")
            topic = self.get_topic(topic_id)
            topic_subscriber.add_topic(topic)
            return topic_subscriber
        return None

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

    def get_request_client(
        self,
        process_id: str,
    ) -> Optional[RequestService]:
        data = self.client.get(f"process:{process_id}:request_client")
        if data:
            request_client = RequestClient.from_json(data)
            requests = self.get_requests(
                f"request_client:{request_client.client_id}:requests:order"
            )
            request_client.add_requests(requests)
            return request_client
        return None

    def get_request_service(
        self,
        process_id: str,
    ) -> Optional[RequestService]:
        data = self.client.get(f"process:{process_id}:request_service")
        if data:
            request_service = RequestService.from_json(data)
            requests = self.get_requests(
                f"request_service:{request_service.service_id}:requests:order"
            )
            request_service.add_requests(requests)
            return request_service
        return None

    def get_user_data(self, user_id: str) -> Optional[UserData]:
        data = self.client.get(f"user_id:{user_id}:data")
        if data:
            return UserData.from_json(data)
        return None

    def is_agent_active(self, agent_id: str) -> bool:
        return self.client.sismember("active_agents", agent_id)

    def set_agent_data(self, agent_data: AgentData):
        self.client.set(
            f"agent:{agent_data.id}",
            agent_data.to_json(),
        )

    def set_agent_process_id(self, agent_id: str, process_name: str, process_id: str):
        self.client.set(
            f"agent:{agent_id}:process_name:{process_name}",
            process_id,
        )
        self.client.set(
            f"process:{process_id}:agent_id",
            agent_id,
        )

    def set_current_process_state(self, process_id: str, process_state: ProcessState):
        self.client.set(
            f"process:{process_id}:current_state",
            process_state.to_json(),
        )

    def set_communications(self, process_id: str, communications: Communications):
        for topic_publisher in communications.topic_publishers:
            self.create_topic_publisher(topic_publisher)
        for topic_subscriber in communications.topic_subscribers:
            self.create_topic_subscriber(process_id, topic_subscriber)
        for request_client in communications.request_clients:
            self.create_request_client(process_id, request_client)
        for request_service in communications.request_services:
            self.create_request_service(process_id, request_service)
        for event_subscriber in communications.event_subscribers:
            self.create_event_subscriber(process_id, event_subscriber)

    def set_process_data(self, process_id: str, process_data: ProcessData):
        self.client.set(
            f"process_data:{process_id}",
            process_data.to_json(),
        )

    def set_process_ids(self, process_ids: ProcessIds):
        self.client.set(
            f"process_ids:{process_ids.process_id}",
            process_ids.to_json(),
        )

    def set_user_data(self, user_data: UserData):
        self.client.set(
            f"user_id:{user_data.user_id}:data",
            user_data.to_json(),
        )

    def set_topic_message(self, topic_id: str, message: Dict[str, Any]):
        topic = self.get_topic(topic_id)
        topic.message = message
        topic.timestamp = get_current_date_iso8601()

        self.client.set(
            f"topic:{topic_id}",
            topic.to_json(),
        )

    def remove_active_agent(self, agent_id: str):
        self.client.srem("active_agents", agent_id)

    def reconstruct_message(self, message_data_str: str) -> JSONMessage:
        message_data_json = json.loads(message_data_str)
        message_type = message_data_json["type"]
        message_json_str = message_data_json["data"]

        message_class: JSONMessage = {
            "UserMessage": UserMessage,
            "AssistantMessage": AssistantMessage,
            "SystemMessage": SystemMessage,
            "ToolResponseMessage": ToolResponseMessage,
            "ToolCalls": ToolCalls,
        }.get(message_type)

        if message_class:
            return message_class.from_json(message_json_str)
        else:
            raise ValueError(f"Unknown message type: {message_type}")

    def update_message(self, message_key: str, message: JSONMessage):
        message_data = json.dumps(
            {"type": type(message).__name__, "data": message.to_json()}
        )
        self.client.hmset(message_key, {"data": message_data})

    def update_request(self, request: Request):
        self.client.set(f"request:{request.id}", request.to_json())
