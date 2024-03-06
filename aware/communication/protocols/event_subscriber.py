from dataclasses import dataclass
import json
from typing import Dict, List

from aware.communication.primitives.event import Event
from aware.communication.primitives.interface.function_detail import FunctionDetail
from aware.communication.protocols.interface.protocol import Protocol


@dataclass
class EventSubscriber(Protocol):
    id: str
    user_id: str
    process_id: str
    event_type_id: str
    event_name: str
    event_description: str
    event_format: Dict[str, str]

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)

    # TODO: Do we need this?
    # def get_event(self) -> str:
    #     events = CommunicationPrimitivesHandler().get_event(self.event_type_id)
    #     return topic.to_string()

    def set_event_comleted(self, success: bool, details: str):
        # TODO: implement this
        pass

    def setup_functions(self) -> List[FunctionDetail]:
        response_format = {"success": "bool", "details": "str"}
        return [
            FunctionDetail(
                name=self.set_event_comleted.__name__,
                args=response_format,
                description="Call this function to set the request completed, filling the args and the success flag.",
                callback=self.set_event_comleted,
            )
        ]
