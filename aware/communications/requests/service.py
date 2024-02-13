import json
from dataclasses import dataclass


@dataclass
class ServiceData:
    def __init__(
        self,
        name: str,
        description: str,
    ):
        self.name = name
        self.description = description

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)


@dataclass
class Service:
    def __init__(
        self,
        service_id: str,
        process_id: str,
        data: ServiceData,
    ):
        self.service_id = service_id
        self.process_id = process_id
        self.data = data

    def to_dict(self):
        return {
            "service_id": self.service_id,
            "process_id": self.process_id,
            "data": self.data.to_json(),
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        data["data"] = ServiceData.from_json(data["data"])
        return cls(**data)
