import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from aware.communications.requests.request import Request


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
        self.request = None

    def _get_highest_prio_request(self, requests: List[Request]):
        # Iterate to find highest priority request.
        highest_prio_request: Optional[Request] = None
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

    def add_requests(self, requests: List[Request]):
        self.request = self._get_highest_prio_request(requests)

    def get_request_query(self) -> Optional[str]:
        if self.request:
            return self.request.query_to_string()
        return None

    def get_set_request_completed_function(self) -> Dict[str, Any]:
        # Add success flag and details to the response format
        self.data.response_format["success"] = "bool"
        self.data.response_format["details"] = "str"
        return {
            "name": "set_request_completed",
            "args": self.data.response_format,
            "description": "Call this function to set the request completed, filling the args and the success flag.",
        }

    def get_send_feedback_function(self) -> Dict[str, Any]:
        # TODO: Should we always add the possibility to send_feedback? This should be enable only if the request is async.
        return {
            "name": "send_feedback",
            "args": self.data.feedback_format,
            "description": "Call this function to send feedback to the client with the specific feedback.",
        }
