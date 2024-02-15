from dataclasses import dataclass
from enum import Enum
import json


class RequestStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"
    WAITING_USER_FEEDBACK = "waiting_user_feedback"


@dataclass
class RequestData:
    def __init__(
        self,
        query: str,
        is_async: bool,
        feedback: str,
        status: RequestStatus,
        response: str,
    ):
        self.query = query
        self.is_async = is_async
        self.status = status
        self.feedback = feedback
        self.response = response

    def to_dict(self):
        return {
            "query": self.query,
            "is_async": self.is_async,
            "status": self.status.value,
            "feedback": self.feedback,
            "response": self.response,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        data["status"] = RequestStatus(data["status"])
        return cls(**data)

    def feedback_to_string(self):
        return f"Query: {self.query}\nFeedback: {self.feedback}"

    def query_to_string(self):
        return f"Request: {self.query}"


@dataclass
class Request:
    def __init__(
        self,
        request_id: str,
        service_id: str,
        service_process_id: str,
        client_process_id: str,
        client_process_name: str,
        timestamp: str,
        data: RequestData,
    ):
        self.id = request_id
        self.service_id = service_id
        self.service_process_id = service_process_id
        self.client_process_id = client_process_id
        self.client_process_name = client_process_name
        self.timestamp = timestamp
        self.data = data

    def to_dict(self):
        return {
            "id": self.id,
            "service_id": self.service_id,
            "service_process_id": self.service_process_id,
            "client_process_id": self.client_process_id,
            "client_process_name": self.client_process_name,
            "timestamp": self.timestamp,
            "data": self.data.to_json(),
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        data["data"] = RequestData.from_json(data["data"])
        return cls(**data)

    def is_async(self) -> bool:
        return self.data.is_async

    def feedback_to_string(self) -> str:
        return self.data.feedback_to_string()

    def query_to_string(self) -> str:
        return self.data.query_to_string()
