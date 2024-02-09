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
from aware.communications.requests.request import Request
from aware.communications.requests.service import Service
from aware.communications.subscriptions.subscription import Subscription
from aware.process.process_data import ProcessData
from aware.process.process_ids import ProcessIds
from aware.process.process import Process
from aware.process.process_communications import ProcessCommunications
from aware.utils.helpers import (
    convert_timestamp_to_epoch,
)


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

    def add_active_process(self, process_id: str):
        self.client.sadd("active_processes", process_id)

    def clear_conversation_buffer(self, process_id: str):
        self.client.delete(f"conversation_buffer:{process_id}")

    def create_subscription(self, process_id: str, subscription: Subscription):
        # Key for storing the serialized subscription
        subscription_key = f"subscription:{subscription.id}"

        # Key for the sorted set to maintain the order of subscriptions by timestamp
        subscription_process_order_key = f"process:{process_id}:subscriptions:order"

        self.client.set(subscription_key, subscription.to_json())

        timestamp = convert_timestamp_to_epoch(subscription.timestamp)
        self.client.zadd(
            subscription_process_order_key,
            {subscription.id: timestamp},
        )

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

    def delete_request(self, request: Request):
        self.client.delete(f"request:{request.id}")
        self.client.zrem(
            f"service_process:{request.service_process_id}:requests:order", request.id
        )
        if request.is_async():
            self.client.zrem(
                f"client_process:{request.client_process_id}:request:order", request.id
            )

    def delete_message(self, process_id: str, message_id: str):
        # The key for the specific message
        message_key = f"conversation:{process_id}:message:{message_id}"

        # Remove the hash storing the message details
        self.client.delete(message_key)

        # Remove the message reference from the sorted set
        conversation_key = f"conversation:{process_id}"
        self.client.zrem(conversation_key, message_key)

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

    def get_process(self, process_ids: ProcessIds) -> Optional[Process]:
        process_communications = self.get_process_communications(
            process_id=process_ids.process_id
        )
        process_data = self.get_process_data(process_id=process_ids.process_id)
        agent_data = self.get_agent_data(agent_id=process_ids.agent_id)

        if process_data and agent_data:
            return Process(
                client_handlers=self,
                ids=process_ids,
                process_communications=process_communications,
                process_data=process_data,
                agent_data=agent_data,
            )
        return None

    def get_process_communications(
        self, process_id: str
    ) -> Optional[ProcessCommunications]:
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
        subscriptions = self.get_subscriptions(process_id)
        # TODO: Add events!
        return ProcessCommunications(
            outgoing_requests=outgoing_requests,
            incoming_request=incoming_request,
            incoming_event=None,
            subscriptions=subscriptions,
        )

    def get_process_data(self, process_ids: ProcessIds) -> Optional[ProcessData]:
        data = self.client.get(f"process_data:{process_ids}")
        if data:
            return ProcessData.from_json(data)
        return None

    def get_subscriptions(self, process_id: str) -> List[Subscription]:
        subscription_order_key = f"process:{process_id}:subscriptions:order"
        # Retrieve all subscriptions IDs from the sorted set, ordered by timestamp
        subscription_ids = self.client.zrange(subscription_order_key, 0, -1)

        subscriptions = []
        for subscription_id_bytes in subscription_ids:
            subscription_id = subscription_id_bytes.decode("utf-8")

            # Fetch the subscription data for each subscription ID and deserialize it
            subscription_data_json = self.client.get(f"subscription:{subscription_id}")
            if subscription_data_json:
                subscriptions.append(
                    Subscription.from_json(subscription_data_json.decode("utf-8"))
                )

        return subscriptions

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

    def get_service(
        self,
        service_id: str,
    ) -> Optional[Service]:
        data = self.client.get(f"service:{service_id}")
        if data:
            return Service.from_json(data)
        return None

    def get_user_data(self, user_id: str) -> Optional[UserData]:
        data = self.client.get(f"user_id:data:{user_id}")
        if data:
            return UserData.from_json(data)
        return None

    # TODO: Remove, should be part of process!
    def get_tools_class(self, process_id: str) -> Optional[str]:
        data = self.client.get(f"tools_class:{process_id}")
        if data:
            return data.decode()
        return None

    def get_topic_data(self, user_id: str, topic_name: str) -> Optional[str]:
        data = self.client.get(f"user_id:{user_id}:topic:{topic_name}")
        if data:
            return data.decode()
        return None

    def is_process_active(self, process_id: str) -> bool:
        return self.client.sismember("active_processes", process_id)

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

    def set_process_data(self, process_id: str, process_data: ProcessData):
        self.client.set(
            f"process_data:{process_id}",
            process_data.to_json(),
        )

    def set_process_communications(
        self, process_id: str, process_communications: ProcessCommunications
    ):
        if process_communications.incoming_request:
            self.create_request(process_communications.incoming_request)
        for request in process_communications.outgoing_requests:
            self.create_request(request)
        for subscription in process_communications.subscriptions:
            self.create_subscription(process_id, subscription)
        # TODO: Add events!

    def set_process(self, process: Process):
        self.set_process_data(process.ids.process_id, process.process_data)
        self.set_process_communications(
            process.ids.process_id, process.process_communications
        )
        self.set_agent_data(process.ids.agent_id, process.agent_data)

    def set_service(
        self,
        service: Service,
    ):
        self.client.set(
            f"service:{service.id}",
            service.to_json(),
        )

    # TODO: Remove, should be part of process!
    def set_tools_class(self, process_id: str, tools_class: str):
        self.client.set(
            f"tools_class:{process_id}",
            tools_class,
        )

    def set_user_data(self, user_data: UserData):
        self.client.set(
            f"user_id:{user_data.user_id}:data",
            user_data.to_json(),
        )

    def set_topic_data(self, user_id: str, topic_name, topic_data: str):
        self.client.set(
            f"user_id:{user_id}:topic:{topic_name}",
            topic_data,
        )

    def remove_active_process(self, process_id: str):
        self.client.srem("active_processes", process_id)

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
