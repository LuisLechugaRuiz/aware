from typing import Dict

from aware.agent.agent_builder import AgentBuilder as SystemAgentBuilder
from aware.process.process_info import ProcessInfo
from aware.tools.tools import Tools


class AgentBuilder(Tools):
    """As agent_builder your task is to select the right configuration needed to create an agent to accomplish the request description"""

    def __init__(
        self,
        process_info: ProcessInfo,
    ):
        super().__init__(process_info=process_info)
        self.agent_builder = SystemAgentBuilder(user_id=self.process_ids.user_id)

    def set_tools(self):
        return [self.create_instructions, self.create_profile]

    def create_instructions(self, instructions: str):
        """Provide a specific instruction explaining to the agent how to combine his tools to accomplish the task. Add also general guidelines and constraints"""
        # Save instructions

    def create_profile(self, fields: Dict[str, str]):
        """Create a specific profile for the agent providing a Dict where the keys are the fields and the values are the description of each field. This profile will be filled with historical information from the agent history and will be shared with the agent to optimize his performance. Consider this profile the most relevant info that the agnet should have access to based on his interactions"""
        # Save profile
