import json
from redis import Redis
from typing import List, Optional, Tuple

from aware.agent.agent import Agent
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

    def delete_message(self, process_id: str, message_id: str):
        # The key for the specific message
        message_key = f"conversation:{process_id}:message:{message_id}"

        # Remove the hash storing the message details
        self.client.delete(message_key)

        # Remove the message reference from the sorted set
        conversation_key = f"conversation:{process_id}"
        self.client.zrem(conversation_key, message_key)

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        data = self.client.get(f"agent:{agent_id}")
        if data:
            return Agent.from_json(data)
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

    def get_user_data(self, user_id: str) -> Optional[UserData]:
        data = self.client.get(f"user_data:{user_id}")
        if data:
            return UserData.from_json(data)
        return None

    def get_tools_class(self, process_id: str) -> Optional[str]:
        data = self.client.get(f"tools_class:{process_id}")
        if data:
            return data.decode()
        return None

    def set_agent(self, agent: Agent):
        self.client.set(
            f"agent:{agent.id}",
            agent.to_json(),
        )

    def set_tools_class(self, process_id: str, tools_class: str):
        self.client.set(
            f"tools_class:{process_id}",
            tools_class,
        )

    def set_user_data(self, user_data: UserData):
        self.client.set(
            f"user_data:{user_data.user_id}",
            user_data.to_json(),
        )

    # def get_message(self, conversation_id: str, message_id: str):
    #     key = f"conversation:{conversation_id}:message:{message_id}"
    #     message_data = self.client.hgetall(key)
    #     if not message_data:
    #         return None

    #     message_type = message_data[b"type"].decode()
    #     message_json = message_data[b"data"].decode()

    #     return self.reconstruct_message(message_type, message_json)

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
