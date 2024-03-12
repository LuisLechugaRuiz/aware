from dataclasses import dataclass
import json
from typing import Any, Dict, List
from pathlib import Path

from aware_use_cases import get_template_config_path, get_user_config_path


@dataclass
class AgentConfigFiles:
    communication: Dict[str, Any]
    config: Dict[str, Any]
    profile: Dict[str, Any]
    state_machine: Dict[str, Any]
    
@dataclass
class CommunicationConfigFiles:
    actions: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    requests: List[Dict[str, Any]]
    topics: List[Dict[str, Any]]


# TODO: In the future we should have organization_id also to maintain teams for multiple users.
class ConfigLoader:
    def __init__(self, template_name: str, user_id: str):
        self.template_path = get_template_config_path(template_name)
        self.user_path = get_user_config_path(user_id)

    def get_file(file_path: Path) -> Dict[str, Any]:
        if file_path.exists():
            with open(file_path, "r") as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"File not found: {file_path}")

    def get_agent_files(self, agent_id: str) -> AgentConfigFiles:
        agent_path = self.template_path / 'agents' / agent_id
        config_files = ['communication.json', 'config.json', 'profile.json', 'state_machine.json']
        data = {}

        for file_name in config_files:
            file_path = agent_path / file_name
            try:
                data[file_name.split('.')[0]] = self.get_file(file_path)
            except FileNotFoundError as e:
                print(f"Warning: {e}")

        return AgentConfigFiles(**data)

    def get_communication_primitives(self) -> CommunicationConfigFiles:
        # TODO: Extract all communications from actions/events/requests/topics and build them properly
        # using CommunicationConfig as with AgentConfig!!
        
        
        return CommunicationConfigFiles

    def get_all_agents_files(self) -> Dict[str, AgentConfigFiles]:
        agents_path = self.template_path / 'agents'
        agents_config = {}

        for agent_folder in [f for f in agents_path.iterdir() if f.is_dir()]:
            agent_id = agent_folder.name
            agents_config[agent_id] = self.get_agent_files(agent_id)

        return agents_config
