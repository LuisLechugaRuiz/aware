import json
from typing import Any, Dict, List, Optional

from aware.agent.agent_data import AgentData
from aware.process.process_data import ProcessData
from aware.process.process_ids import ProcessIds
from aware.requests.request import Request


class ProcessInterface:
    def __init__(
        self,
        ids: ProcessIds,
        process_data: ProcessData,
        agent_data: AgentData,
        outgoing_requests: List[Request],
        incoming_request: Optional[Request],
    ):
        self.ids = ids
        self.process_data = process_data
        self.agent_data = agent_data
        self.outgoing_requests = outgoing_requests
        self.incoming_request = incoming_request

    def get_meta_prompt_kwargs(self) -> Dict[str, Any]:
        meta_kwargs = {}
        if self.outgoing_requests:
            # Add the feedback of all the outgoing requests
            requests_feedback = "\n".join(
                [request.feedback_to_string() for request in self.outgoing_requests]
            )
            meta_kwargs.update({"outgoing_requests": requests_feedback})
        if self.incoming_request is not None:
            # Add the query of the incoming request
            meta_kwargs.update(
                {"incoming_request": self.incoming_request.query_to_string()}
            )

        # TODO: Add here also events!
        return meta_kwargs

    def get_prompt_kwargs(self) -> Dict[str, Any]:
        return self.agent_data.to_dict()

    def to_dict(self):
        return {
            "ids": self.ids.to_dict(),
            "process_data": self.process_data.to_dict(),
            "agent_data": json.loads(self.agent_data.to_json()),
            "outgoing_requests": [
                json.loads(request.to_json()) for request in self.outgoing_requests
            ],
            "incoming_request": (
                json.loads(self.incoming_request.to_json())
                if self.incoming_request
                else None
            ),
        }

    def to_json(self):
        return json.dumps(
            self.to_dict(),
            default=lambda o: o.__dict__ if hasattr(o, "__dict__") else str(o),
        )

    @staticmethod
    def from_json(json_str: str):
        data = json.loads(json_str)
        data["ids"] = ProcessIds.from_json(json.dumps(data["ids"]))
        data["process_data"] = ProcessData.from_json(json.dumps(data["prompt_data"]))
        data["agent_data"] = AgentData.from_json(json.dumps(data["agent_data"]))
        data["outgoing_requests"] = [
            Request.from_json(json.dumps(request))
            for request in data["outgoing_requests"]
        ]
        data["incoming_request"] = (
            Request.from_json(json.dumps(data["incoming_request"]))
            if data["incoming_request"]
            else None
        )
        return ProcessData(**data)
