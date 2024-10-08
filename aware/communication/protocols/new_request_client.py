from dataclasses import dataclass
import json
from typing import Any, Dict, List

from aware.agent.agent_data import NewAgentState
from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)
from aware.communication.primitives.request import Request
from aware.communication.protocols.interface.protocol import Protocol
from aware.database.helpers import DatabaseResult
from aware.communication.primitives.interface.function_detail import FunctionDetail


@dataclass
class RequestClientConfig:
    service_name: str

    def to_json(self):
        return {
            "service_name": self.service_name
        }

    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)


class RequestClient(Protocol):
    def __init__(
        self,
        id: str,
        user_id: str,
        process_id: str,
        process_name: str,
        service_id: str,
        service_name: str,
        service_description: str,
        request_format: Dict[str, Any],
    ):
        self.user_id = user_id
        self.process_id = process_id
        self.process_name = process_name
        self.service_id = service_id
        self.service_name = service_name
        self.service_description = service_description
        self.request_format = request_format
        self.primitives_database_handler = PrimitivesDatabaseHandler()
        super().__init__(id=id)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "process_id": self.process_id,
            "process_name": self.process_name,
            "service_id": self.service_id,
            "service_name": self.service_name,
            "service_description": self.service_description,
            "request_format": self.request_format,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str: str) -> "RequestClient":
        data = json.loads(json_str)
        return RequestClient(**data)

    def create_request(
        self,
        request_message: Dict[str, Any],
        priority: int,
    ) -> DatabaseResult[Request]:
        # - Save request in database
        request = self.primitives_database_handler.create_request(
            client_id=self.id,
            request_message=request_message,
            priority=priority,
        )
        if request.error:
            return f"Error creating request: {request.error}"
        self.send_communication(task_name="create_request", primitive_str=request.data.to_json())
        # TODO: Update agent data to set it to: NewAgentState.WAITING_FOR_RESPONSE
        return "Request created successfully."

    @property
    def tools(self) -> List[FunctionDetail]:
        self.request_format["priority"] = "int"
        return [
            FunctionDetail(
                name=self.service_name,
                args=self.request_format,
                description=f"Call this function to send a request to a service with the following description: {self.service_description}",
                callback=self.create_request,
            )
        ]
        


# New request client, with the things that the model really needs to know.

class NewRequestClient
    # This would be only for Autonomous agents, where the agents can select the communications freely.
    # For some cases we want more control stablishing the communications and fixing the execution.
    # This should be an agent for autonomous mode.
    
    # This means that we need to create requests replicating the logic that we use to create client and server, but just adding them on demand.

    def create_request(agent_name: str, query: str, response_format: Dict[str, Any], is_async: bool, priority: int) -> DatabaseResult[Request]:
        # Steps: 1 -> Search agent_name and create a new service.
        
        #  - Find agent by name.
        # 2. Create a new request with specific format.
