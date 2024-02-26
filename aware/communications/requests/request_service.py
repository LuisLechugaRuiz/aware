import json
from dataclasses import dataclass


@dataclass
class RequestServiceData:
    name: str
    description: str
    request_name: str  # TODO: Should this be the name or the full request?
    tool_name: str

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "request": self.request_name,
            "tool_name": self.tool_name,
        }

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)


class RequestService:
    def __init__(
        self, user_id: str, process_id: str, service_id: str, data: RequestServiceData
    ):
        self.user_id = user_id
        self.process_id = process_id
        self.service_id = service_id
        self.data = data

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "process_id": self.process_id,
            "service_id": self.service_id,
            "data": self.data.to_dict(),
        }

    def to_json(self):
        return json.dumps(self.__dict__)

    @staticmethod
    def from_json(json_str: str):
        data = json.loads(json_str)
        data["data"] = RequestServiceData.from_json(data["data"])
        return RequestService(**data)
