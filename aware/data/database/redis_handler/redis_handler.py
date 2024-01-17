import json
from redis import Redis
from typing import List, Optional, Tuple

from aware.agent.memory.new_working_memory import WorkingMemory
from aware.chat.new_conversation_schemas import (
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

    def get_working_memory(self, user_id: str) -> Optional[WorkingMemory]:
        data = self.client.get(f"working_memory:{user_id}")
        if data:
            return WorkingMemory.from_json(data)
        return None

    def set_working_memory(self, working_memory: WorkingMemory):
        self.client.set(
            f"working_memory:{working_memory.user_id}",
            working_memory.to_json(),
        )

    def add_message(
        self,
        chat_id: str,
        chat_message: ChatMessage,
    ):
        message = chat_message.message
        key = f"conversation:{chat_id}:message:{chat_message.message_id}"
        message_data = json.dumps(
            {"type": type(message).__name__, "data": message.to_json()}
        )
        self.client.hmset(key, {"data": message_data})

        # Add the key to the sorted set with timestamp as the score
        conversation_key = f"conversation:{chat_id}"
        self.client.zadd(
            conversation_key, {key: convert_timestamp_to_epoch(chat_message.timestamp)}
        )

    def delete_message(self, chat_id: str, message_id: str):
        # The key for the specific message
        message_key = f"conversation:{chat_id}:message:{message_id}"

        # Remove the hash storing the message details
        self.client.delete(message_key)

        # Remove the message reference from the sorted set
        conversation_key = f"conversation:{chat_id}"
        self.client.zrem(conversation_key, message_key)

    # TODO: Check if conversation exists, return None otherwise.
    def get_conversation(self, chat_id: str) -> List[JSONMessage]:
        conversation_key = f"conversation:{chat_id}"

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

    def add_call_info(self, call_info: CallInfo):
        self.client.set(
            f"call_info:{call_info.call_id}",
            call_info.to_json(),
        )
        self.client.lpush("pending_call", call_info.call_id)

    def get_api_key(self, user_id: str) -> Optional[str]:
        return self.client.get(f"api_key:{user_id}")

    def get_call_info(self, call_id: str) -> CallInfo:
        data = CallInfo.from_json(self.client.get(f"call_info:{call_id}"))
        data.set_conversation(self.get_conversation(data.chat_id))

        data.set_api_key(self.get_api_key(data.user_id).decode())
        return data

    def get_pending_call(self) -> Optional[Tuple[str, str]]:
        return self.client.brpop("pending_call", timeout=10)

    def set_api_key(self, user_id: str, api_key: str):
        self.client.set(f"api_key:{user_id}", api_key)

    def store_response(self, call_id: str, response: str):
        self.client.set(f"response:{call_id}", response)