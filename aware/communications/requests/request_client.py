import json
from typing import Any, Dict, List

from aware.chat.parser.json_pydantic_parser import JsonPydanticParser
from aware.communications.requests.request import Request


class RequestClient:
    def __init__(
        self,
        user_id: str,
        process_id: str,
        process_name: str,
        client_id: str,
        service_id: str,
        service_name: str,
        service_description: str,
        request_format: Dict[str, Any],
        requests: List[Request],
    ):
        self.user_id = user_id
        self.process_id = process_id
        self.process_name = process_name

        self.client_id = client_id
        self.service_id = service_id
        self.service_name = service_name
        self.service_description = service_description
        self.request_format = request_format
        self.requests = requests

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "process_id": self.process_id,
            "process_name": self.process_name,
            "client_id": self.client_id,
            "service_id": self.service_id,
            "service_name": self.service_name,
            "service_description": self.service_description,
            "request_format": self.request_format,
            "requests": [request.to_dict() for request in self.requests],
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def from_json(json_str: str):
        data = json.loads(json_str)
        data["requests"] = [Request.from_json(request) for request in data["requests"]]
        return RequestClient(**data)

    def get_request_as_function(self) -> Dict[str, Any]:
        self.request_format["is_async"] = "bool"
        request_description = f"Call this function to send a request to the a service with the following description: {self.service_description}"
        return JsonPydanticParser.get_function_schema(
            name=self.service_name,
            args=self.request_format,
            description=request_description,
        )

    def get_request_feedback(self) -> str:
        return self.requests[0].feedback_to_string()
