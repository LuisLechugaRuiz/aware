import json
from dataclasses import dataclass


@dataclass
class ServiceData:
    def __init__(
        self,
        name: str,
        description: str,
        prompt_prefix: str,
    ):
        self.name = name
        self.description = description
        self.prompt_prefix = prompt_prefix

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
        self.id = service_id
        self.process_id = process_id
        self.data = data

    def to_dict(self):
        return {
            "id": self.id,
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
