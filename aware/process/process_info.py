import json
from dataclasses import dataclass
from typing import List

from aware.agent.agent_data import AgentData
from aware.communications.communications import Communications
from aware.process.process_data import ProcessData
from aware.process.process_ids import ProcessIds
from aware.process.state_machine.state import ProcessState


@dataclass
class ProcessInfo:
    agent_data: AgentData
    communications: Communications
    process_ids: ProcessIds
    process_data: ProcessData
    process_states: List[ProcessState]
    current_state: ProcessState

    def to_dict(self):
        return {
            "agent_data": self.agent_data.to_dict(),
            "communications": self.communications.to_dict(),
            "process_ids": self.process_ids.to_dict(),
            "process_data": self.process_data.to_dict(),
            "process_states": [state.to_dict() for state in self.process_states],
            "current_state": self.current_state.to_dict(),
        }

    def to_json(self):
        return json.dumps(
            self.to_dict(),
            default=lambda o: o.__dict__ if hasattr(o, "__dict__") else str(o),
        )

    @staticmethod
    def from_json(json_str: str):
        data = json.loads(json_str)
        data["agent_data"] = AgentData.from_json(data["agent_data"])
        data["communication"] = Communications.from_json(data["communications"])
        data["process_ids"] = ProcessIds.from_json(data["process_ids"])
        data["process_data"] = ProcessData.from_json(data["process_data"])
        data["process_states"] = [
            ProcessState.from_json(state) for state in data["process_states"]
        ]
        data["current_state"] = ProcessState.from_json(data["current_state"])
        return ProcessData(**data)

    def get_name(self):
        if self.process_data.name == "main":
            return self.agent_data.name
        else:
            return self.process_data.name
