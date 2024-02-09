import json

from aware.process.process_ids import ProcessIds


class Event:
    def __init__(self, process_ids: ProcessIds):
        self.process_ids = process_ids

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)
