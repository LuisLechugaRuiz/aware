import json
from typing import List, Dict, Any


from aware.chat.new_conversation_schemas import JSONMessage


class CallInfo:
    def __init__(
        self,
        user_id: str,
        call_id: str,
        process_name: str,
        chat_id: str,
        system_message: str,
        functions: List[Dict[str, Any]],
    ):
        self.user_id = user_id
        self.call_id = call_id
        self.process_name = process_name
        self.chat_id = chat_id
        self.system_message = system_message
        self.functions = functions
        self.conversation = None
        self.api_key = None

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)

    def to_json(self):
        return json.dumps(self.__dict__)

    def get_conversation(self):
        return self.conversation

    def set_conversation(self, conversation: List[JSONMessage]):
        self.conversation = conversation

    def get_api_key(self):
        return self.api_key

    def set_api_key(self, api_key: str):
        self.api_key = api_key
