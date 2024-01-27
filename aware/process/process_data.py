import json
from dataclasses import dataclass
from typing import Any, Dict, List

from aware.agent.agent_data import AgentData
from aware.process.prompt_data import PromptData
from aware.process.process_ids import ProcessIds
from aware.requests.request import Request


@dataclass
class ProcessData:
    ids: ProcessIds
    agent_data: AgentData
    prompt_data: PromptData
    requests: List[Request]
    # Add here Events

    def get_meta_prompt_kwargs(self) -> Dict[str, Any]:
        meta_kwargs = {}
        if self.requests:
            request_string = (
                f"{self.requests[0].data.prompt_prefix} {self.requests[0].data.query}"
            )
            meta_kwargs.update({"request": request_string})
        # TODO: Add here also events!
        return meta_kwargs

    def get_prompt_kwargs(self) -> Dict[str, Any]:
        return self.agent_data.to_dict()

    def to_dict(self):
        return {
            "ids": self.ids.to_dict(),
            "agent_data": json.loads(self.agent_data.to_json()),
            "prompt_data": self.prompt_data.to_dict(),
            "requests": [json.loads(request.to_json()) for request in self.requests],
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
        data["agent_data"] = AgentData.from_json(json.dumps(data["agent_data"]))
        data["prompt_data"] = PromptData.from_json(json.dumps(data["prompt_data"]))
        data["requests"] = [
            Request.from_json(json.dumps(request)) for request in data["requests"]
        ]
        return ProcessData(**data)
