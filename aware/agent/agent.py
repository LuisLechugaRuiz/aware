import json
from dataclasses import dataclass

from aware.agent.agent_data import AgentData
from aware.agent.agent_processes import AgentProcesses


@dataclass
class Agent:
    def __init__(self, agent_data: AgentData, agent_processes: AgentProcesses):
        self.data = agent_data
        self.processes = agent_processes

    def to_dict(self):
        combined_dict = {**self.data.to_dict(), **self.processes.to_dict()}
        return combined_dict

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)

        # Extracting AgentData and AgentProcesses parts from the combined data
        data_dict = {k: data[k] for k in AgentData.__annotations__.keys() if k in data}
        processes_dict = {
            k: data[k] for k in AgentProcesses.__annotations__.keys() if k in data
        }

        # Creating AgentData and AgentProcesses instances from their respective parts
        data = AgentData(**data_dict)
        processes = AgentProcesses(**processes_dict)

        return cls(data, processes)
