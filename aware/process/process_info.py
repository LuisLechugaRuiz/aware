import json
from dataclasses import dataclass

from aware.agent.agent_data import AgentData
from aware.process.process_communications import ProcessCommunications
from aware.process.process_data import ProcessData
from aware.process.process_ids import ProcessIds


@dataclass
class ProcessInfo:
    agent_data: AgentData
    process_ids: ProcessIds
    process_data: ProcessData
    process_communications: ProcessCommunications

    def to_dict(self):
        return {
            "agent_data": self.agent_data.to_dict(),
            "process_ids": self.process_ids.to_dict(),
            "process_data": self.process_data.to_dict(),
            "process_communications": self.process_communications.to_dict(),
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
        data["process_ids"] = ProcessIds.from_json(data["process_ids"])
        data["process_data"] = ProcessData.from_json(data["process_data"])
        data["process_communication"] = ProcessCommunications.from_json(
            data["process_communications"]
        )
        return ProcessData(**data)
