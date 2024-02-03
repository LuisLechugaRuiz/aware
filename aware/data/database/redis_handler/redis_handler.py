import json
from redis import Redis
from typing import List, Optional

from aware.agent.agent_data import Agent, AgentData
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
from aware.process.process_data import ProcessData
from aware.process.process_ids import ProcessIds
from aware.process.prompt_data import PromptData
from aware.requests.request import Request
from aware.requests.service import Service
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

    def clear_conversation_buffer(self, process_id: str):
        self.client.delete(f"conversation_buffer:{process_id}")

    def create_request(
        self, service_process_id: str, service_id: str, request: Request
    ):
        # Key for storing the serialized request
        request_data_key = f"service:{service_id}:request:{request.id}"

        # Key for the sorted set to maintain the order of requests by timestamp
        request_order_key = f"process:{service_process_id}:requests:order"

        # Key for mapping request_id to service_id
        request_service_map_key = f"request:{request.id}:service"

        # Convert the request to JSON and store it
        self.client.set(request_data_key, request.to_json())

        # Store the mapping of request_id to service_id
        self.client.set(request_service_map_key, service_id)

        # Add the request ID to the sorted set with the timestamp as the score
        self.client.zadd(
            request_order_key,
            {request.id: convert_timestamp_to_epoch(request.timestamp)},
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

    # TODO: Check if conversation exists, return None otherwise.
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

    def get_process_data(self, process_ids: ProcessIds) -> Optional[ProcessData]:
        agent_data = self.get_agent_data(agent_id=process_ids.agent_id)
        prompt_data = self.get_prompt_data(process_id=process_ids.process_id)
        requests = self.get_requests(process_id=process_ids.process_id)

        if agent_data and prompt_data:
            return ProcessData(
                ids=process_ids,
                agent_data=agent_data,
                prompt_data=prompt_data,
                requests=requests,
            )
        return None

    def get_process_services(self, process_id: str) -> List[Service]:
        service_keys = self.client.keys(f"process:{process_id}:service:*")
        return [
            Service.from_json(self.client.get(service_key))
            for service_key in service_keys
        ]

    def get_prompt_data(self, process_id: str) -> Optional[PromptData]:
        data = self.client.get(f"prompt_data:{process_id}")
        if data:
            return PromptData.from_json(data)
        return None

    def get_requests(self, process_id: str) -> List[Request]:
        # Key pattern for the sorted sets of requests for each service process
        request_order_key = f"process:{process_id}:requests:order"

        # Retrieve all request IDs from the sorted set, ordered by timestamp
        request_ids = self.client.zrange(request_order_key, 0, -1)

        requests = []
        for request_id_bytes in request_ids:
            request_id = request_id_bytes.decode("utf-8")

            # Retrieve the service_id for this request
            service_id = self.client.get(f"request:{request_id}:service").decode(
                "utf-8"
            )
            request = self.get_request(service_id, request_id)
            if request:
                requests.append(request)

        return requests

    def get_request(self, service_id: str, request_id: str) -> Request:
        # Construct the key for the serialized request data
        request_data_key = f"service:{service_id}:request:{request_id}"

        # Fetch the request data for each request ID and deserialize it
        request_data_json = self.client.get(request_data_key)
        if request_data_json:
            return Request.from_json(request_data_json.decode("utf-8"))
        return None

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

    def get_tools_class(self, process_id: str) -> Optional[str]:
        data = self.client.get(f"tools_class:{process_id}")
        if data:
            return data.decode()
        return None

    def get_topic_data(self, user_id: str, topic_name: str) -> Optional[str]:
        data = self.client.get(
            f"user_id:{user_id}:topic:{topic_name}"
        )
        if data:
            return data.decode()
        return None

    # TODO: ADD FUNCTONS: ADD PROCESS TO ACTIVE | REMOVE PROCESS FROM ACTIVE
    def is_process_active(self, process_id: str) -> bool:
        return self.client.exists(f"process:{process_id}:active")

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

    def set_prompt_data(self, process_id: str, prompt_data: PromptData):
        self.client.set(
            f"prompt_data:{process_id}",
            prompt_data.to_json(),
        )

    def set_process_data(self, process_data: ProcessData):
        self.set_agent(process_data.ids.agent_id, process_data.agent_data)
        self.set_prompt_data(process_data.ids.process_id, process_data.prompt_data)
        self.set_requests(process_data.requests)

    def set_requests(self, requests: List[Request]):
        for request in requests:
            self.create_request(request.service_id, request)

    def set_service(
        self,
        service: Service,
    ):
        self.client.set(
            f"service:{service.id}",
            service.to_json(),
        )

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
