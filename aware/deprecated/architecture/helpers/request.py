from enum import Enum
import json
from typing import Optional
import uuid

from aware.utils.communication_protocols.actions.action import Action


class RequestStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"
    WAITING_USER_FEEDBACK = "waiting_user_feedback"
    # CANCELED = "canceled"

    def __init__(self, status: str):
        self.status = status


class Request(Action):
    def __init__(
        self,
        request: str,
        status: Optional[RequestStatus] = RequestStatus.NOT_STARTED,
        feedback: Optional[str] = None,
        id: Optional[int] = None,
    ):
        self.request = request
        self.status = status
        self.feedback = feedback
        self.id = uuid.uuid4().int if id is None else id

    def to_json(self):
        return json.dumps(
            {
                "request": self.request,
                "status": self.status.name,
                "feedback": self.feedback,
                "id": self.id,
            }
        )

    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        return Request(
            request=data["request"],
            status=RequestStatus[data["status"]],
            feedback=data["feedback"],
            id=data["id"],
        )

    def get_feedback(self):
        return self.feedback

    def get_id(self):
        return self.id

    def get_status(self):
        return self.status

    def update_feedback(self, feedback: str):
        self.feedback = feedback

    def update_status(self, status: RequestStatus, feedback: Optional[str] = None):
        self.status = status
        if feedback:
            self.update_feedback(feedback)

    def __str__(self):
        repr = f"Request: {self.request}, status: {self.status}"
        if self.feedback:
            repr += f", feedback: {self.feedback}"
        return repr
