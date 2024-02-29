import json
from redis import Redis
from typing import List, Optional, Tuple

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
from aware.communications.events.event import Event
from aware.communications.events.event_subscriber import EventSubscriber
from aware.communications.events.event_type import EventType
from aware.communications.requests.request import Request
from aware.communications.requests.request_client import RequestClient
from aware.communications.requests.request_service import RequestService
from aware.communications.topics.topic import Topic
from aware.communications.topics.topic_subscriber import TopicSubscriber
from aware.communications.topics.topic_publisher import TopicPublisher
from aware.process.process_data import ProcessData
from aware.process.process_ids import ProcessIds
from aware.process.process_communications import ProcessCommunications
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
        event_data_key = (
            f"user_id:{event.user_id}:event_type:{event.name}:event:{event.id}"
        )
        # Convert the event to JSON and store it
        self.client.set(event_data_key, event.to_json())
        # Order the events by timestamp
        event_order_key = f"user_id:{event.user_id}:event_type:{event.name}:event:order"
        self.client.zadd(
            event_order_key,
            {event_data_key: convert_timestamp_to_epoch(event.timestamp)},
        )

    def create_event_type(self, event_type: EventType):
        event_type_key = f"user_id:{event_type.user_id}:event_type:{event_type.name}"
        self.client.set(event_type_key, event_type.to_json())

    def create_event_subscriber(
        self,
        process_ids: ProcessIds,
        event_subscriber: EventSubscriber,  # This should be event_subscriber
    ):
        # Create a map user-event to process_ids to retrieve the processes subscribed to specific event.
        event_subscription_key = f"user_id:{process_ids.user_id}:event_subscribed:{event_subscriber.event_name}"
        self.client.sadd(event_subscription_key, process_ids.to_json())
        # Create event subscriptions to get the specific events subscribed by the process.
        self.client.sadd(
            f"process:{process_ids.process_id}:event_subscribers",
            event_subscriber.to_json(),
        )

    def create_process_state(self, process_id: str, process_state: ProcessState):
        self.client.sadd(
            f"process:{process_id}:states",
            process_state.to_json(),
        )

    def create_topic(self, topic: Topic):
        self.client.set(
            f"user_id:{topic.user_id}:topic:{topic.name}",
            topic.to_json(),
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

    def create_request_client(self, request_client: RequestClient):
        self.client.sadd(
            f"process:{request_client.process_id}:request_clients",
            request_client.to_json(),
        )

    def create_request_service(self, request_service: RequestService):
        self.client.sadd(
            f"process:{request_service.process_id}:request_service",
            request_service.to_json(),
        )
        self.client.sadd(
            f"request_service:{request_service.service_id}", request_service.to_json()
        )

    # TODO: refactor with new client/services
    def create_request(self, request: Request):
        # Key for storing the serialized request
        request_data_key = f"request:{request.id}"

        # Key for the sorted set to maintain the order of requests by timestamp
        request_service_order_key = (
            f"service_process:{request.service_process_id}:requests:order"
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
                f"client_process:{request.client_process_id}:request:order"
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
            f"service_process:{request.service_process_id}:requests:order", request.id
        )
        if request.is_async():
            self.client.zrem(
                f"client_process:{request.client_process_id}:request:order", request.id
            )

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

    def get_events(self, user_id: str, event_name: str) -> List[Event]:
        event_order_key = f"user_id:{user_id}:event_type:{event_name}:event:order"
        event_keys = self.client.zrange(event_order_key, 0, -1)

        events = []
        for event_key in event_keys:
            event_data = self.client.get(event_key)
            events.append(Event.from_json(event_data))
        return events

    def get_event_subscriptions(self, process_id: str) -> List[Event]:
        event_subscriptions = self.client.smembers(
            f"process:{process_id}:event_subscriptions"
        )
        events = []
        for event_subscription_str in event_subscriptions:
            event_subscription = EventSubscription.from_json(event_subscription_str)
            events.extend(
                self.get_events(
                    event_subscription.user_id, event_subscription.event_name
                )
            )
        return events

    # TODO: REFACTOR!
    def get_process_communications(self, process_id: str) -> ProcessCommunications:
        #
        self.get_request_service(service_id=process_id)

        outgoing_requests = self.get_requests(
            f"client_process:{process_id}:request:order"
        )
        incoming_requests = self.get_requests(
            f"service_process:{process_id}:requests:order"
        )
        if len(incoming_requests) > 0:
            incoming_request = incoming_requests[0]
        else:
            incoming_request = None

        events = self.get_event_subscriptions(process_id)
        if len(events) > 0:
            event = events[0]
        else:
            event = None

        topics = self.get_subscribed_topics(process_id)
        return ProcessCommunications(
            outgoing_requests=outgoing_requests,
            incoming_request=incoming_request,
            event=event,
            topics=topics,
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

    def get_processes_subscribed_to_event(
        self, user_id: str, event: Event
    ) -> List[ProcessIds]:
        event_subscription_key = f"user_id:{user_id}:event_subscribed:{event.name}"
        process_ids = [
            ProcessIds.from_json(process_id)
            for process_id in self.client.smembers(event_subscription_key)
        ]
        return process_ids

    def get_topic(self, user_id: str, topic_name: str) -> Optional[Topic]:
        data = self.client.get(f"user_id:{user_id}:topic:{topic_name}")
        if data:
            return Topic.from_json(data)
        return None

    def get_subscribed_topics(self, process_id: str) -> List[Topic]:
        topic_subscribers = self.client.smembers(
            f"process:{process_id}:topic_subscribers"
        )
        topics = []
        for topic_subscriber_str in topic_subscribers:
            topic_subscriber = TopicSubscriber.from_json(topic_subscriber_str)
            topic = self.get_topic(
                user_id=topic_subscriber.user_id,
                topic_name=topic_subscriber.topic_name,
            )
            topics.append(topic)
        return topics

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

    def get_request_service(
        self,
        service_id: str,
    ) -> Optional[RequestService]:
        data = self.client.get(f"request_service:{service_id}")
        if data:
            return RequestService.from_json(data)
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

    def set_process_communications(
        self, process_id: str, process_communications: ProcessCommunications
    ):
        if process_communications.incoming_request:
            self.create_request(process_communications.incoming_request)
        for request in process_communications.outgoing_requests:
            self.create_request(request)

        # TODO: Get topic subscribers from process_communications instead of forming them here.
        for topic in process_communications.topics:
            topic_subscriber = TopicSubscriber(
                user_id=topic.user_id,
                process_id=process_id,
                topic_id=topic.id,
                topic_name=topic.topic_name,
            )
            self.create_topic_subscriber(process_id, topic_subscriber)

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

    def set_topic_content(self, user_id: str, topic_name: str, content: str):
        topic = self.get_topic(user_id, topic_name)
        topic.content = content
        topic.timestamp = get_current_date_iso8601()

        self.client.set(
            f"user_id:{user_id}:topic:{topic_name}",
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
