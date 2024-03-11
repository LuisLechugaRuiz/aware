import json
from typing import Dict, List, Optional

from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)
from aware.communication.primitives.event import Event
from aware.communication.primitives.interface.function_detail import FunctionDetail
from aware.communication.protocols.interface.input_protocol import InputProtocol


class EventSubscriber(InputProtocol):
    def __init__(
        self,
        id: str,
        user_id: str,
        process_id: str,
        event_type_id: str,
        event_name: str,
        event_description: str,
        event_format: Dict[str, str],
    ):
        self.user_id = user_id
        self.event_type_id = event_type_id
        self.event_name = event_name
        self.event_description = event_description
        self.event_format = event_format
        super().__init__(id=id, process_id=process_id)

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)

    def add_input(self, input: Event):
        self.current_event = input

    def get_input(self) -> Optional[Event]:
        return self.current_event

    def get_inputs(self) -> List[Event]:
        return PrimitivesDatabaseHandler().get_events(self.event_type_id)

    def set_input_completed(self):
        self.set_event_comleted(response={}, success=True)

    def set_event_comleted(self, details: str, success: bool):
        if self.current_event:
            PrimitivesDatabaseHandler().set_event_completed(event=self.current_event, details=details, success=success)
            self.remove_current_input()
            return "Event completed."
        raise ValueError("No event to complete.")

    @property
    def tools(self) -> List[FunctionDetail]:
        response_format = {"success": "bool", "details": "str"}
        return [
            FunctionDetail(
                name=self.set_event_comleted.__name__,
                args=response_format,
                description="Call this function to set the request completed, filling the args and the success flag.",
                callback=self.set_event_comleted,
            )
        ]
