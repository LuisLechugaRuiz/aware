from dataclasses import dataclass
import json


@dataclass
class RequestData:
    def __init__(
        self,
        query: str,
        is_async: bool,
        feedback: str,
        status: str,
        response: str,
        prompt_prefix: str,
    ):
        self.query = query
        self.is_async = is_async
        self.status = status
        self.feedback = feedback
        self.response = response
        self.prompt_prefix = prompt_prefix

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)

    def feedback_to_string(self):
        return f"Query: {self.query}\nFeedback: {self.feedback}"

    def query_to_string(self):
        return f"{self.prompt_prefix} {self.query}"


@dataclass
class Request:
    def __init__(
        self,
        request_id: str,
        service_id: str,
        service_process_id: str,
        client_process_id: str,
        timestamp: str,
        data: RequestData,
    ):
        self.id = request_id
        self.service_id = service_id
        self.service_process_id = service_process_id
        self.client_process_id = client_process_id
        self.timestamp = timestamp
        self.data = data

    def to_dict(self):
        return {
            "id": self.id,
            "service_id": self.service_id,
            "service_process_id": self.service_process_id,
            "client_process_id": self.client_process_id,
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
