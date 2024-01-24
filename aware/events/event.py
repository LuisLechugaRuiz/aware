import json


class Event:
    def __init__(self, chat_id: str, user_id: str):
        self.chat_id = chat_id
        self.user_id = user_id

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)
