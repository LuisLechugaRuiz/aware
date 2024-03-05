import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from aware.communication.primitives.request import Request
from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)


@dataclass
class RequestServiceData:
    service_name: str
    service_description: str
    request_format: Dict[str, Any]
    feedback_format: Dict[str, Any]
    response_format: Dict[str, Any]
    tool_name: str

    def to_dict(self):
        return {
            "service_name": self.service_name,
            "service_description": self.service_description,
            "request_format": self.request_format,
            "feedback_format": self.feedback_format,
            "response_format": self.response_format,
            "tool_name": self.tool_name,
        }

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)


class RequestService:
    def __init__(
        self, user_id: str, process_id: str, service_id: str, data: RequestServiceData
    ):
        self.user_id = user_id
        self.process_id = process_id
        self.service_id = service_id
        self.data = data
        self.current_request = self._get_highest_prio_request()

    def _get_highest_prio_request(self) -> Optional[Request]:
        # Iterate to find highest priority request.
        highest_prio_request: Optional[Request] = None
        requests = PrimitivesDatabaseHandler().get_service_requests(self.service_id)
        for request in requests:
            if (
                highest_prio_request is None
                or request.data.priority > highest_prio_request.data.priority
            ):
                highest_prio_request = request
        return highest_prio_request

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "process_id": self.process_id,
            "service_id": self.service_id,
            "data": self.data.to_dict(),
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str: str) -> "RequestService":
        data = json.loads(json_str)
        data["data"] = RequestServiceData.from_json(data["data"])
        return RequestService(**data)

    def get_request_query(self) -> Optional[str]:
        if self.current_request:
            return self.current_request.query_to_string()
        return None

    def get_set_request_completed_function(self) -> Dict[str, Any]:
        self.data.response_format["success"] = "bool"
        self.data.response_format["details"] = "str"
        return {
            "name": "set_request_completed",
            "args": self.data.response_format,
            "description": "Call this function to set the request completed, filling the args and the success flag.",
        }

    def get_send_feedback_function(self) -> Dict[str, Any]:
        return {
            "name": "send_feedback",
            "args": self.data.feedback_format,
            "description": "Call this function to send feedback to the client with the specific feedback.",
        }

    def set_request_completed(self, response: Dict[str, Any], success: bool):
        if self.current_request:
            return PrimitivesDatabaseHandler().set_request_completed(
                self.current_request, success, response
            )
        return None
