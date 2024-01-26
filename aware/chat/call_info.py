import json
from typing import Any, Dict, List, Optional


from aware.chat.conversation_schemas import JSONMessage, SystemMessage


class CallInfo:
    def __init__(
        self,
        user_id: str,
        process_id: str,
        call_id: str,
        process_name: str,
        system_message: str,
        functions: List[Dict[str, Any]],
        agent_name: Optional[str] = None,
    ):
        self.user_id = user_id
        self.process_id = process_id
        self.call_id = call_id

        self.process_name = process_name
        self.system_message = system_message
        self.functions = functions

        if agent_name is not None:
            self.agent_name = agent_name
        else:
            self.agent_name = self.process_name

        self.conversation = None
        self.api_key = None

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "process_id": self.process_id,
            "call_id": self.call_id,
            "process_name": self.process_name,
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
