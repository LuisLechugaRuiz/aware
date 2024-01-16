import json
import abc

from typing import Any, Dict, List


class JSONMessage(abc.ABC):
    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)

    def to_dict(self):
        return self.__dict__.copy()

    @abc.abstractmethod
    def to_string(self):
        pass

    @abc.abstractmethod
    def to_openai_dict(self) -> Dict[str, Any]:
        pass


class UserMessage(JSONMessage):
    def __init__(self, name: str, content: str):
        self.role = "user"
        self.name = name
        self.content = content

    def to_string(self):
        return f"{self.role} ({self.name}): {self.content}"

    def to_dict(self):
        return {"name": self.name, "content": self.content}

    def to_openai_dict(self):
        return {"role": self.role, "name": self.name, "content": self.content}


class AssistantMessage(JSONMessage):
    def __init__(self, name: str, content: str):
        self.role = "assistant"
        self.name = name
        self.content = content

    def to_string(self):
        return f"{self.role} ({self.name}): {self.content}"

    def to_dict(self):
        return {"name": self.name, "content": self.content}

    def to_openai_dict(self):
        return {"role": self.role, "name": self.name, "content": self.content}


class SystemMessage(JSONMessage):
    def __init__(self, content: str):
        self.role = "system"
        self.content = content

    def to_string(self):
        return f"{self.role}: {self.content}"

    def to_dict(self):
        return {"content": self.content}

    def to_openai_dict(self):
        return {"role": self.role, "content": self.content}


class ToolResponseMessage(JSONMessage):
    def __init__(self, content: str, tool_call_id: str):
        self.role = "tool"
        self.content = content
        self.tool_call_id = tool_call_id

    def to_string(self):
        return f"{self.role} (ID: {self.tool_call_id}): {self.content}"

    def to_openai_dict(self):
        return {
            "role": self.role,
            "content": self.content,
            "tool_call_id": self.tool_call_id,
        }


class Function(JSONMessage):
    def __init__(self, arguments: str, name: str):
        self.arguments = arguments
        self.name = name

    def to_string(self):
        return f"{self.name}({self.arguments})"

    def to_openai_dict(self):
        return {
            "arguments": self.arguments,
            "name": self.name,
        }


class ToolCall(JSONMessage):
    def __init__(self, id: str, type: str, function: Function):
        self.id = id
        self.type = type
        self.function = function

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        data["function"] = Function(**data["function"])
        return cls(**data)

    def to_dict(self):
        data = super().to_dict()
        data["function"] = self.function.to_dict()  # Convert nested Function object
        return data

    def to_string(self):
        return f"ToolCall({self.id}, {self.type}, {self.function.to_string()})"

    def to_openai_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "function": self.function.to_dict(),
        }


class ToolCalls(JSONMessage):
    def __init__(self, name: str, tool_calls: List[ToolCall]):
        self.role = "assistant"
        self.name = name
        self.tool_calls = tool_calls

    def to_dict(self):
        data = {"name": self.name}
        data["tool_calls"] = self.tool_calls_to_dict()
        return data

    def tool_calls_to_dict(self):
        return [tool_call.to_dict() for tool_call in self.tool_calls]

    def to_string(self):
        return f"{self.role} ({self.name}): {json.dumps(self.tool_calls_to_dict())}"

    def to_openai_dict(self):
        return {
            "role": self.role,
            "name": self.name,
            "tool_calls": self.tool_calls_to_dict(),
        }

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        data["tool_calls"] = [
            ToolCall.from_json(json.dumps(tc)) for tc in data["tool_calls"]
        ]
        return cls(**data)


class ChatMessage(JSONMessage):
    def __init__(self, message_id: str, timestamp: str, message: JSONMessage):
        self.message_id = message_id
        self.timestamp = timestamp
        self.message = message

    def to_string(self):
        return self.message.to_string()

    def to_json(self):
        data = super().to_dict()
        data["message"] = self.message.to_dict()  # Convert nested JSONMessage object
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str, json_message_class=JSONMessage):
        data = json.loads(json_str)
        data["message"] = json_message_class.from_json(json.dumps(data["message"]))
        return cls(**data)

    def to_openai_dict(self):
        return {
            "message": self.message.to_openai_dict(),
        }
