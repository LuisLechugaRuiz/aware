from typing import Dict, List

from aware.agent.agent_builder import AgentBuilder as InternalAgentBuilder
from aware.agent.database.agent_database_handler import AgentDatabaseHandler
from aware.process.process_info import ProcessInfo
from aware.tool.tools import Tools


class AgentBuilder(Tools):
    """As agent_builder your task is to select the right configuration needed to create an agent to accomplish the request description"""

    def __init__(
        self,
        process_info: ProcessInfo,
    ):
        super().__init__(process_info=process_info)
        self.agent_builder = InternalAgentBuilder(user_id=self.process_ids.user_id)
        # TODO: implement tool database handlers.
        self.agent_state = ClientHandlers().get_stored_variable(process_ids=self.process_ids, variable_name="agent_state") # TODO: Implement me, verify if we need agent_state as local var, probably should be used just on the process creation.

    def set_tools(self):
        return [
            self.create_agent,
            self.create_profile,
        ]

    # This function will be called as request so we should not include it in the toolkit of the agent!

    # TODO: REMOVE! HAS BEEN TRANSLATED TO REQUEST.
    # def create_agent(self, name: str, tools: str, task: str, instructions: str):
    #     """
    #     Create a new agent which satisfies the request description.

    #     Args:
    #         name (str): Agent's name, a specific variable name used to describe the agent, will be used to identify the agent. Should follow convention: lower followed by "_".
    #         tools (str): The tools that the agent should use to accomplish the next step.
    #         task (str): Agent's task, a highlevel description of his mission, should be general to solve similar requests.
    #         instructions (str): Specific instructions or recommendations about possible combinations of tool executions that could be performed to satisfy the requests.
    #     """
    #     try:
    #         self.agent_builder.create_agent(
    #             name=name,
    #             capability_class=tools,
    #             task=task,
    #             instructions=instructions,
    #         )
    #         return f"Agent {name} created successfully"
    #     except Exception as e:
    #         return f"Error creating agent {name}: {e}"

    # TODO: Define the correct states to create process state machine. Define how to show the states in the prompt.
    def create_state(self, state_name: str, task: str, instructions: str, tools: List[str]):



    def create_profile(self, name: str, fields: Dict[str, str]):
        """Create a specific profile for the agent providing a Dict where the keys are the fields and the values are the description of each field. This profile will be filled with historical information from the agent history and will be shared with the agent to optimize his performance. Consider this profile the most relevant info that the agnet should have access to based on his interactions
        Args:
            name (str): Agent's name, a specific variable name used to describe the agent, will be used to identify the agent. Should follow convention: lower followed by "_".
            profile (Dict[str, str]): A dictionary with the fields and their descriptions.
        """
        # TODO: Implement me
        self.agent_builder.set_profile(name, fields)

    # TODO: Implement me when agent builder is created in the concept of teams, to identify the services we need to understand the relationship between agents.
    # def create_service(self, name: str, fields: Dict[str, str]):
