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
class ActionServiceConfig:
    service_name: str
    service_description: str
    action_name: str

    def to_json(self):
        return {
            "service_name": self.service_name,
            "service_description": self.service_description,
            "action_name": self.action_name,
        }

    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)


@dataclass
class ActionServiceData:
    service_name: str
    service_description: str
    request_format: Dict[str, str]
    feedback_format: Dict[str, str]
    response_format: Dict[str, str]
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
        self.data = data
        super().__init__(id=id, process_id=process_id)

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

    def add_input(self, input: Action):
        self.current_action = input

    def get_input(self) -> Optional[Action]:
        return self.current_action

    def send_action_feedback(self, feedback: Dict[str, Any]):
        if self.current_action:
            PrimitivesDatabaseHandler().send_action_feedback(
                self.current_action, feedback
            )
            self.send_communication(task_name="send_action_feedback", primitive_str=self.current_action.to_json())
            return "Feedback sent."
        raise ValueError("No action to send feedback to.")

    def set_input_completed(self):
        # TODO: Fill self.data.response_format with dummy data. To don't break the logic while checking response format.
        self.set_action_completed(response={}, success=True)

    def set_action_completed(
        self, response: Dict[str, Any], success: bool
    ):
        if self.current_action:
            PrimitivesDatabaseHandler().set_action_completed(
                self.current_action, response, success
            )
            self.remove_current_input()
            self.send_communication(task_name="set_action_completed", primitive_str=self.current_action.to_json())
            return "Action set as completed."
        raise ValueError("No action to set as completed.")

    def get_inputs(self) -> List[Action]:
        return PrimitivesDatabaseHandler().get_service_actions(self.id)

    @property
    def tools(self) -> List[FunctionDetail]:
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
                name=self.send_action_feedback.__name__,
                args=self.data.feedback_format,
                description="Call this function to send feedback to the action client.",
                callback=self.send_action_feedback,
            ),
        ]
