import json
from typing import Any, Dict, List

from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)
from aware.communication.primitives.interface.function_detail import FunctionDetail
from aware.communication.protocols.interface.protocol import Protocol


class ActionClient(Protocol):
    def __init__(
        self,
        id: str,
        user_id: str,
        process_id: str,
        process_name: str,
        service_id: str,
        service_name: str,
        service_description: str,
        request_format: Dict[str, Any],
    ):
        self.user_id = user_id
        self.process_id = process_id
        self.process_name = process_name

        self.service_id = service_id
        self.service_name = service_name
        self.service_description = service_description
        self.request_format = request_format
        self.primitives_database_handler = PrimitivesDatabaseHandler()
        super().__init__(id=id)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "process_id": self.process_id,
            "process_name": self.process_name,
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

    def get_action_feedback(self) -> str:
        actions = self.primitives_database_handler.get_client_actions(self.id)
        return "\n".join([action.feedback_to_string() for action in actions])

    def create_action(self, request_message: Dict[str, Any], priority: int):
        # - Save request in database
        result = self.primitives_database_handler.create_action(
            client_id=self.id,
            request_message=request_message,
            priority=priority,
        )
        if result.error:
            return f"Error creating action: {result.error}"
        return "Action created successfully."

    @property
    def tools(self) -> List[FunctionDetail]:
        self.request_format["priority"] = "int"
        return [
            FunctionDetail(
                name=self.service_name,
                args=self.request_format,
                description=f"Call this function to send an action (will be managed asynchronously) to a service with the following description: {self.service_description}",
                callback=self.create_action,
                should_continue=True,
            )
        ]
