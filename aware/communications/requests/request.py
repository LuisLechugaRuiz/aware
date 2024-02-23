from dataclasses import dataclass
from enum import Enum
import json
from typing import Any, Dict, Optional

from aware.tools.tools_manager import ToolsManager


class RequestStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"
    WAITING_USER_FEEDBACK = "waiting_user_feedback"


@dataclass
class RequestData:
    request_message: Dict[str, Any]
    is_async: bool
    feedback: str
    status: RequestStatus
    response: str

    def to_dict(self):
        return {
            "request_message": self.request_message,
            "is_async": self.is_async,
            "status": self.status.value,
            "feedback": self.feedback,
            "response": self.response,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        data["status"] = RequestStatus(data["status"])
        return cls(**data)

    # TODO: Define how to translate the request_message from json to string
    def feedback_to_string(self):
        return f"Request: {self.request_message}\nFeedback: {self.feedback}"

    def query_to_string(self):
        return f"Request: {self.request_message}"


# TODO: Remove dataclasss and edit it to start agent when this function is called.
@dataclass
class Request:
    def __init__(
        self,
        request_id: str,
        service_id: str,
        service_process_id: str,
        client_process_id: str,
        client_process_name: str,
        timestamp: str,
        data: RequestData,
        tool: Optional[str] = None,
    ):
        self.id = request_id
        self.service_id = service_id
        self.service_process_id = service_process_id
        self.client_process_id = client_process_id
        self.client_process_name = client_process_name
        self.timestamp = timestamp
        self.data = data
        self.tool = tool

    def to_dict(self):
        return {
            "id": self.id,
            "service_id": self.service_id,
            "service_process_id": self.service_process_id,
            "client_process_id": self.client_process_id,
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

    def is_async(self) -> bool:
        return self.data.is_async

    def feedback_to_string(self) -> str:
        return self.data.feedback_to_string()

    def query_to_string(self) -> str:
        return self.data.query_to_string()

    # TODO: Implement me!!
    def call(self, request_message: Dict[str, Any]) -> str:
        if self.tool is not None:
            requests_registry = RequestsRegistry(["requests"])
            requests_registry.get_request(self.tool).call(request_message)
