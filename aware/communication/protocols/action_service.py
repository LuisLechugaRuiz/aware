import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from aware.communication.primitives.action import Action
from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)
from aware.communication.primitives.interface.function_detail import FunctionDetail
from aware.communication.protocols.interface.protocol import Protocol


@dataclass
class ActionServiceData:
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


class ActionService(Protocol):
    def __init__(
        self, user_id: str, process_id: str, service_id: str, data: ActionServiceData
    ):
        self.user_id = user_id
        self.process_id = process_id
        self.service_id = service_id
        self.data = data
        # TODO: address me properly.
        self.current_action = self._get_highest_prio_action()

    def _get_highest_prio_action(self) -> Optional[Action]:
        # Iterate to find highest action request.
        highest_prio_action: Optional[Action] = None
        requests = PrimitivesDatabaseHandler().get_service_actions(self.service_id)
        for request in requests:
            if (
                highest_prio_action is None
                or request.data.priority > highest_prio_action.data.priority
            ):
                highest_prio_action = request
        return highest_prio_action

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
    def from_json(json_str: str) -> "ActionService":
        data = json.loads(json_str)
        data["data"] = ActionServiceData.from_json(data["data"])
        return ActionServiceData(**data)

    def get_action_query(self) -> Optional[str]:
        if self.current_action:
            return self.current_action.query_to_string()
        return None

    def send_feedback(self, feedback: Dict[str, Any]):
        if self.current_action:
            return PrimitivesDatabaseHandler().send_action_feedback(
                self.current_action, feedback
            )
        return None

    def set_action_completed(self, response: Dict[str, Any], success: bool):
        if self.current_action:
            # TODO: address me properly.
            return PrimitivesDatabaseHandler().set_action_completed(
                self.current_action, response, success
            )
        return None

    def setup_functions(self) -> List[FunctionDetail]:
        self.data.response_format["success"] = "bool"
        self.data.response_format["details"] = "str"
        return [
            FunctionDetail(
                name=self.set_action_completed.__name__,
                args=self.data.response_format,
                description="Call this function to set the action completed, filling the args and the success flag.",
                callback=self.set_action_completed,
            ),
            FunctionDetail(
                name=self.send_feedback.__name__,
                args=self.data.feedback_format,
                description="Call this function to send feedback to the action client.",
                callback=self.send_feedback,
            ),
        ]
