import json


class UserMessage:
    def __init__(self, user_name: str, message: str):
        self.user_name = user_name
        self.message = message

    def to_json(self):
        return json.dumps(
            {
                "user_name": self.user_name,
                "message": self.message,
            }
        )

    @staticmethod
    def from_json(json_str):
        json_dict = json.loads(json_str)
        return UserMessage(
            user_name=json_dict["user_name"],
            message=json_dict["message"],
        )


class UserContextMessage:
    def __init__(self, user_message: UserMessage, context: str, thought: str):
        self.user_message = user_message
        self.context = context
        self.thought = thought

    def to_json(self):
        return json.dumps(
            {
                "user_message": self.user_message.to_json(),
                "context": self.context,
                "thought": self.thought,
            }
        )

    @staticmethod
    def from_json(json_str):
        json_dict = json.loads(json_str)
        return UserContextMessage(
            user_message=UserMessage.from_json(json_dict["user_message"]),
            context=json_dict["context"],
            thought=json_dict["thought"],
        )
