import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from aware.communication.primitives.action import Action
from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)
from aware.communication.primitives.interface.function_detail import FunctionDetail
from aware.communication.protocols.interface.input_protocol import InputProtocol


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


class ActionService(InputProtocol):
    def __init__(self, id: str, user_id: str, process_id: str, data: ActionServiceData):
        self.user_id = user_id
        self.process_id = process_id
        self.data = data
        super().__init__(id=id)

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
    def from_json(json_str: str) -> "ActionService":
        data = json.loads(json_str)
        data["data"] = ActionServiceData.from_json(data["data"])
        return ActionServiceData(**data)

    # TODO: Do we need this? Now are using generic input_to_prompt_string to get the query of any of possible inputs.
    def get_action_query(self) -> Optional[str]:
        if self.current_action:
            return self.current_action.query_to_string()
        return None

    # TODO: refactor to receive the input (action) as arg.
    def send_feedback(self, action: Action, feedback: Dict[str, Any]):
        if self.current_action:
            return PrimitivesDatabaseHandler().send_action_feedback(
                self.current_action, feedback
            )
        return None

    def set_action_completed(
        self, action: Action, response: Dict[str, Any], success: bool
    ):
        if self.current_action:
            # TODO: address me properly.
            return PrimitivesDatabaseHandler().set_action_completed(
                self.current_action, response, success
            )
        return None

    def get_inputs(self) -> List[Action]:
        return PrimitivesDatabaseHandler().get_service_actions(self.id)

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
