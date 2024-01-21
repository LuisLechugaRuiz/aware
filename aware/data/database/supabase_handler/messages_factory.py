import json

from aware.chat.conversation_schemas import (
    ChatMessage,
    UserMessage,
    AssistantMessage,
    SystemMessage,
    ToolResponseMessage,
    ToolCalls,
)


class MessagesFactory:
    @staticmethod
    def create_message(row):
        message_type = row.get("message_type")
        content = row.get("content")

        json_message = None
        if message_type == "UserMessage":
            json_message = UserMessage(name=row.get("name"), content=content)
        elif message_type == "AssistantMessage":
            json_message = AssistantMessage(name=row.get("name"), content=content)
        elif message_type == "SystemMessage":
            json_message = SystemMessage(content=content)
        elif message_type == "ToolResponseMessage":
            json_message = ToolResponseMessage(
                content=content, tool_call_id=row.get("tool_call_id")
            )
        elif message_type == "ToolCalls":
            json_message = ToolCalls.from_json(json.dumps(row.get("tool_calls")))
        else:
            raise ValueError(f"Unknown message type: {message_type}")
        return ChatMessage(
            message_id=row.get("id"),
            timestamp=row.get("created_at"),
            message=json_message,
        )
