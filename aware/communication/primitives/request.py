from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional
import json

from aware.communication.primitives.interface.input import Input
from aware.chat.conversation_schemas import UserMessage


class RequestStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class RequestData:
    request: Dict[str, Any]
    response: Dict[str, Any]
    priority: int
    status: RequestStatus

    def to_dict(self):
        return {
            "request": self.request,
            "response": self.response,
            "priority": self.priority,
            "status": self.status.value,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        data["status"] = RequestStatus(data["status"])
        return cls(**data)

    def query_to_string(self):
        return f"Request: {self.dict_to_string(self.request)}"

    def response_to_string(self):
        return f"Response: {self.dict_to_string(self.response)}"

    def dict_to_string(self, dict: Dict[str, Any]):
        return "\n".join([f"{key}: {value}" for key, value in dict.items()])


# TODO: Do we need all these variables?
class Request(Input):
    def __init__(
        self,
        service_id: str,
        service_process_id: str,
        service_name: str,
        client_id: str,
        client_process_id: str,
        client_process_name: str,
        timestamp: str,
        data: RequestData,
        tool: Optional[str] = None,
    ):
        self.service_id = service_id
        self.service_process_id = service_process_id
        self.service_name = service_name
        self.client_process_id = client_process_id
        self.client_id = client_id
        self.client_process_name = client_process_name
        self.timestamp = timestamp
        self.data = data
        self.tool = tool
        super().__init__(id=request_id, priority=self.data.priority)

    def to_dict(self):
        return {
            "id": self.id,
            "service_id": self.service_id,
            "service_process_id": self.service_process_id,
            "service_name": self.service_name,
            "client_process_id": self.client_process_id,
            "client_id": self.client_id,
            "client_process_name": self.client_process_name,
            "timestamp": self.timestamp,
            "data": self.data.to_json(),
            "tool": self.tool if self.tool else None,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        data["data"] = RequestData.from_json(data["data"])
        data["tool"] = data["tool"] if data["tool"] else None
        return cls(**data)

    # TODO: Do we need it? now we are using input_to_prompt_string.
    def query_to_string(self) -> str:
        return self.data.query_to_string()

    def input_to_prompt_string(self) -> str:
        return self.data.query_to_string()

    def is_completed(self) -> bool:
        return self.data.status in [RequestStatus.SUCCESS, RequestStatus.FAILURE]

    def response_to_string(self) -> str:
        return self.data.response_to_string()

    def get_type(self) -> str:
        return "request"

    def input_to_user_message(self) -> UserMessage:
        return UserMessage(
            name=self.client_process_name,
            content=f"Received the following request: {self.input_to_prompt_string()}",
        )
