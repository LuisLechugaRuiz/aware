import json
from dataclasses import dataclass

from aware.process.process_ids import ProcessIds


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
        self, process_ids: ProcessIds, service_id: str, data: RequestServiceData
    ):
        self.process_ids = process_ids
        self.service_id = service_id
        self.data = data

    def to_dict(self):
        return {
            "process_ids": self.process_ids.to_dict(),
            "service_id": self.service_id,
            "data": self.data.to_dict(),
        }

    def to_json(self):
        return json.dumps(self.__dict__)

    @staticmethod
    def from_json(json_str: str):
        data = json.loads(json_str)
        data["process_ids"] = ProcessIds.from_json(data["process_ids"])
        data["data"] = RequestServiceData.from_json(data["data"])
        return RequestService(**data)
