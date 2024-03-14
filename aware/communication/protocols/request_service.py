from dataclasses import dataclass
import json
from typing import Any, Dict, List, Optional

from aware.communication.primitives.request import Request
from aware.communication.primitives.interface.function_detail import FunctionDetail
from aware.communication.protocols.interface.input_protocol import InputProtocol


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


class RequestService(InputProtocol):
    def __init__(
        self,
        id: str,
        user_id: str,
        process_id: str,
        data: RequestServiceData,
    ):
        self.user_id = user_id
        self.data = data
        super().__init__(id=id, process_id=process_id)

    def get_inputs(self) -> List[Request]:
        return self.primitive_database_handler.get_service_requests(self.id)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "process_id": self.process_id,
            "data": self.data.to_dict(),
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str: str) -> "RequestService":
        data = json.loads(json_str)
        data["data"] = RequestServiceData.from_json(data["data"])
        return RequestService(**data)

    def add_input(self, input: Request):
        self.current_request = input

    def get_input(self) -> Optional[Request]:
        return self.current_request

    def set_input_completed(self):
        self.set_request_completed(response={}, success=True)

    def set_request_completed(self, response: Dict[str, Any], success: bool):
        if self.current_request:
            self.primitive_database_handler.set_request_completed(
                self.current_request, response, success
            )
            self.remove_current_input()
            self.send_communication(task_name="set_request_completed", primitive_str=self.current_request.to_json())
            return f"Request {self.current_request.id} completed."
        raise ValueError("No current request to set completed.")

    @property
    def tools(self) -> List[FunctionDetail]:
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
