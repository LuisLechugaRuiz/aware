import json


class UserMessage:
    def __init__(self, user_name: str, message: str):
        self.user_name = user_name
        self.message = message

    def to_json(self):
        return json.dumps({"user_name": self.user_name, "message": self.message})

    @staticmethod
    def from_json(json_str):
        json_dict = json.loads(json_str)
        return UserMessage(
            user_name=json_dict["user_name"], message=json_dict["message"]
        )
