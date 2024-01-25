import json


class Event:
    def __init__(self, user_id: str, process_id: str):
        self.user_id = user_id
        self.process_id = process_id

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)
