import json
from typing import List, Dict, Any


from aware.chat.conversation_schemas import JSONMessage, SystemMessage


class CallInfo:
    def __init__(
        self,
        user_id: str,
        call_id: str,
        chat_id: str,
        process_name: str,
        agent_name: str,
        system_message: str,
        functions: List[Dict[str, Any]],
    ):
        self.user_id = user_id
        self.call_id = call_id
        self.chat_id = chat_id
        self.process_name = process_name
        self.agent_name = agent_name
        self.system_message = system_message
        self.functions = functions
        self.conversation = None
        self.api_key = None

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "call_id": self.call_id,
            "chat_id": self.chat_id,
            "process_name": self.process_name,
            "agent_name": self.agent_name,
            "system_message": self.system_message,
            "functions": self.functions,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def get_conversation_messages(self) -> Dict[str, Any]:
        openai_messages = [SystemMessage(self.system_message).to_openai_dict()]
        openai_messages += [message.to_openai_dict() for message in self.conversation]
        return openai_messages

    def set_conversation(self, conversation: List[JSONMessage]):
        self.conversation = conversation

    def get_api_key(self):
        return self.api_key

    def set_api_key(self, api_key: str):
        self.api_key = api_key
