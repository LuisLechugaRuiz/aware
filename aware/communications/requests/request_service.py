import json
from dataclasses import dataclass
from typing import Any, Dict

from aware.chat.parser.json_pydantic_parser import JsonPydanticParser


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

    def request_to_function(self) -> Dict[str, Any]:
        request_description = f"Call this function to send a request to the a service with the following description: {self.service_description}"
        return JsonPydanticParser.get_function_schema(
            name=self.service_name,
            args=self.request_format,
            description=request_description,
        )


class RequestService:
    def __init__(
        self, user_id: str, process_id: str, service_id: str, data: RequestServiceData
    ):
        self.user_id = user_id
        self.process_id = process_id
        self.service_id = service_id
        self.data = data

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "process_id": self.process_id,
            "service_id": self.service_id,
            "data": self.data.to_dict(),
        }

    def to_json(self):
        return json.dumps(self.__dict__)

    @staticmethod
    def from_json(json_str: str):
        data = json.loads(json_str)
        data["data"] = RequestServiceData.from_json(data["data"])
        return RequestService(**data)
