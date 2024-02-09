import json
from typing import Any, Dict, Optional

from aware.agent.agent_data import AgentData
from aware.communications.requests.request import Request
from aware.process.process_data import ProcessData
from aware.process.process_ids import ProcessIds
from aware.process.process_communications import ProcessCommunications


class ProcessInterface:
    def __init__(
        self,
        ids: ProcessIds,
        process_data: ProcessData,
        process_communications: ProcessCommunications,
        agent_data: AgentData,
    ):
        self.ids = ids
        self.process_data = process_data
        self.process_communications = process_communications
        self.agent_data = agent_data

    def get_prompt_kwargs(self) -> Dict[str, Any]:
        prompt_kwargs = self.process_data.to_prompt_kwargs()
        prompt_kwargs.update(self.process_communications.to_prompt_kwargs())
        prompt_kwargs.update(self.agent_data.to_prompt_kwargs())
        return prompt_kwargs

    def get_current_request(self) -> Optional[Request]:
        return self.process_communications.incoming_request

    def to_dict(self):
        return {
            "ids": self.ids.to_dict(),
            "process_data": self.process_data.to_dict(),
            "process_communications": self.process_communications.to_dict(),
            "agent_data": json.loads(self.agent_data.to_json()),
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
        data["process_communications"] = ProcessCommunications.from_json(
            json.dumps(data["process_communications"])
        )
        data["agent_data"] = AgentData.from_json(json.dumps(data["agent_data"]))
        return ProcessData(**data)
