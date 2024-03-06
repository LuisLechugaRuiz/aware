import json
from typing import Any, Dict

from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)
from aware.communication.primitives.request import Request
from aware.communication.protocols.interface.protocol import Protocol
from aware.database.helpers import DatabaseResult


class RequestClient(Protocol):
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
    ):
        self.user_id = user_id
        self.process_id = process_id
        self.process_name = process_name

        self.client_id = client_id
        self.service_id = service_id
        self.service_name = service_name
        self.service_description = service_description
        self.request_format = request_format
        self.primitives_database_handler = PrimitivesDatabaseHandler()

        # TODO: improve this.
        super().__init__()
        self.setup_functions()

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
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str: str) -> "RequestClient":
        data = json.loads(json_str)
        return RequestClient(**data)

    def create_request(
        self,
        request_message: Dict[str, Any],
        priority: int,
    ) -> DatabaseResult[Request]:
        # - Save request in database
        return self.primitives_database_handler.create_request(
            client_id=self.client_id,
            request_message=request_message,
            priority=priority,
        )

    def setup_functions(self):
        self.request_format["priority"] = "int"
        request_description = f"Call this function to send a request to a service with the following description: {self.service_description}"
        self.register_function(
            name=self.service_name,
            args=self.request_format,
            description=request_description,
            callback=self.create_request,
        )
