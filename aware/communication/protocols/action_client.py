import json
from typing import Any, Dict

from aware.chat.parser.json_pydantic_parser import JsonPydanticParser

from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)
from aware.communication.primitives.action import Action
from aware.database.helpers import DatabaseResult


class ActionClient:
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
    def from_json(json_str: str) -> "ActionClient":
        data = json.loads(json_str)
        return ActionClient(**data)

    def get_action_as_function(self) -> Dict[str, Any]:
        self.request_format["priority"] = "int"

        action_description = f"Call this function to send an action (will be managed asynchronously) to a service with the following description: {self.service_description}"
        return JsonPydanticParser.get_function_schema(
            name=self.service_name,
            args=self.request_format,
            description=action_description,
        )

    def get_action_feedback(self) -> str:
        actions = self.primitives_database_handler.get_client_actions(self.client_id)
        return "\n".join([action.feedback_to_string() for action in actions])

    def create_action(
        self, request_message: Dict[str, Any], priority: int
    ) -> DatabaseResult[Action]:
        # - Save request in database
        return self.primitives_database_handler.create_action(
            client_id=self.client_id,
            request_message=request_message,
            priority=priority,
        )
