from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional
import json


class RequestStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"
    WAITING_USER_FEEDBACK = "waiting_user_feedback"  # TODO: Verify if needed.


@dataclass
class RequestData:
    request: Dict[str, Any]
    feedback: Dict[str, Any]
    response: Dict[str, Any]
    priority: int
    is_async: bool
    status: RequestStatus

    def to_dict(self):
        return {
            "request": self.request,
            "feedback": self.feedback,
            "response": self.response,
            "priority": self.priority,
            "is_async": self.is_async,
            "status": self.status.value,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        data["status"] = RequestStatus(data["status"])
        return cls(**data)

    def feedback_to_string(self):
        return f"Request: {self.dict_to_string(self.request)}\nFeedback: {self.dict_to_string(self.feedback)}"

    def query_to_string(self):
        return f"Request: {self.dict_to_string(self.request)}"

    def dict_to_string(self, dict: Dict[str, Any]):
        return "\n".join([f"{key}: {value}" for key, value in dict.items()])


class Request:
    def __init__(
        self,
        request_id: str,
        service_id: str,
        service_process_id: str,
        client_id: str,
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
        self.client_id = client_id
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

    def is_async(self) -> bool:
        return self.data.is_async

    def feedback_to_string(self) -> str:
        return self.data.feedback_to_string()

    def query_to_string(self) -> str:
        return self.data.query_to_string()