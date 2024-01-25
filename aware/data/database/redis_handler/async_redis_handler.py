import json
from aioredis import Redis
from typing import List, Optional, Tuple

from aware.memory.user.user_data import UserData
from aware.chat.conversation_schemas import (
    JSONMessage,
    UserMessage,
    AssistantMessage,
    SystemMessage,
    ToolResponseMessage,
    ToolCalls,
)
from aware.chat.call_info import CallInfo


class AsyncRedisHandler:
    def __init__(self, client: Redis):
        self.client = client

    # TODO: Check if conversation exists, return None otherwise.
    async def get_conversation(self, process_id: str) -> List[JSONMessage]:
        conversation_key = f"conversation:{process_id}"

        # Retrieve all message keys from the sorted set, ordered by timestamp
        message_keys = await self.client.zrange(conversation_key, 0, -1)

        messages = []
        for message_key in message_keys:
            message_data = await self.client.hget(message_key, "data")
            if message_data:
                message_data_str = message_data
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

    async def get_api_key(self, user_id: str) -> Optional[str]:
        user_data = await self.get_user_data(user_id)
        if user_data:
            return user_data.api_key
        return None

    async def get_call_info(self, process_id: str) -> CallInfo:
        data = CallInfo.from_json(await self.client.get(f"call_info:{process_id}"))
        data.set_conversation(await self.get_conversation(data.process_id))

        data.set_api_key(await self.get_api_key(data.user_id))
        return data

    async def get_user_data(self, user_id: str) -> Optional[UserData]:
        data = await self.client.get(f"user_data:{user_id}")
        if data:
            return UserData.from_json(data)
        return None

    async def get_pending_call(self) -> Optional[Tuple[str, str]]:
        return await self.client.brpop("pending_call", timeout=10)

    async def store_response(self, call_id: str, response: str):
        await self.client.set(f"response:{call_id}", response)
