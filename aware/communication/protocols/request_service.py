import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from aware.communication.primitives.request import Request
from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)
from aware.communication.primitives.interface.function_detail import FunctionDetail
from aware.communication.protocols.interface.protocol import Protocol


@dataclass
class RequestServiceData:
    service_name: str
    service_description: str
    request_format: Dict[str, Any]
    response_format: Dict[str, Any]
    tool_name: str

    def to_dict(self):
        return {
            "service_name": self.service_name,
            "service_description": self.service_description,
            "request_format": self.request_format,
            "response_format": self.response_format,
            "tool_name": self.tool_name,
        }

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)


class RequestService(Protocol):
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

    def set_request_completed(self, response: Dict[str, Any], success: bool):
        if self.current_request:
            PrimitivesDatabaseHandler().set_request_completed(
                self.current_request, response, success
            )
            # TODO: send here to CommunicationDispatcher to process set_request_completed! Use celery to send the task.
        return f"Request {self.current_request.id} completed."

    def setup_functions(self) -> List[FunctionDetail]:
        self.data.response_format["success"] = "bool"
        self.data.response_format["details"] = "str"
        return [
            FunctionDetail(
                name=self.set_request_completed.__name__,
                args=self.data.response_format,
                description="Call this function to set the request completed, filling the args and the success flag.",
                callback=self.set_request_completed,
            )
        ]
