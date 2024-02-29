# Merge this minimal implementation with the requirements of the request (processes ids and other internal data needed).
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict
import json

from aware.chat.parser.json_pydantic_parser import JsonPydanticParser


class RequestStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"
    WAITING_USER_FEEDBACK = "waiting_user_feedback"  # TODO: Verify if needed.


# TODO: Define the representation of the dicts into prompt.
@dataclass
class RequestData:
    request: Dict[str, Any]
    feedback: Dict[str, Any]
    response: Dict[str, Any]
    is_async: bool
    status: RequestStatus

    def to_dict(self):
        return {
            "request": self.request,
            "feedback": self.feedback,
            "response": self.response,
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
        return f"Request: {self.request}\nFeedback: {self.feedback}"

    def query_to_string(self):
        return f"Request: {self.request}"


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
        format: RequestFormat,
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

    # TODO: Add these new vars to request. We need to have access to format - to create the function. Service_name for the function name and description from service name to describe why to use this request for.
    def to_function(self):
        # Present the function info as a dict to be interpreted by OpenAI.
        request_description = "Specific Intro for request" + self.service_description
        return JsonPydanticParser.get_function_schema(
            name=self.service_name,
            args=self.format.request_format,
            description=self.service_description,
        )
