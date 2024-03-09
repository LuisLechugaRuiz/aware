from typing import Any, Dict

from aware.agent.agent_builder import AgentBuilder as InternalAgentBuilder
from aware.process.process_info import ProcessInfo
from aware.tools.tools import Tools

# TODO: Implement me
# TWO OPTIONS:
# BY CONFIG -> WE CREATE THE REQUESTS AND WE CALL INTERNAL FUNCTIONS

# BY AGENT_BUILDER -> IN THIS CASE INSTEAD OF CREATING A NEW CLASS WE JUST USE IT TO COMMUNICATE AGENT TO AGENT SO WE CALL FUNCTION DEFAULT REQUEST.
class TeamBuilder(Tools):
    """As agent_builder your task is to select the right configuration needed to create an agent to accomplish the request description"""

    def __init__(
        self,
        process_info: ProcessInfo,
    ):
        super().__init__(process_info=process_info)
        self.agent_builder = InternalAgentBuilder(user_id=self.process_ids.user_id)


    def create_client(self, agent_id: str, service_name: str, request_message: Dict[str, Any]):

    def create_server(self, agent_id: str, service_name: str, response_message: Dict[str, Any]):
        
    def create_publisher(self, agent_id: str, topic_name: str, message: Dict[str, Any]):

    def create_subscriber(self, agent_id: str, topic_name: str):




    def set_tools(self):
        return [
            self.create_agent,
            self.create_profile,
        ]

    # This function will be called as request so we should not include it in the toolkit of the agent!
    def create_agent(self, name: str, tools: str, task: str, instructions: str):
        """
        Create a new agent which satisfies the request description.

        Args:
            name (str): Agent's name, a specific variable name used to describe the agent, will be used to identify the agent. Should follow convention: lower followed by "_".
            tools (str): The tools that the agent should use to accomplish the next step.
            task (str): Agent's task, a highlevel description of his mission, should be general to solve similar requests.
            instructions (str): Specific instructions or recommendations about possible combinations of tool executions that could be performed to satisfy the requests.
        """
        try:
            self.agent_builder.create_agent(
                name=name,
                capability_class=tools,
                task=task,
                instructions=instructions,
            )
            return f"Agent {name} created successfully"
        except Exception as e:
            return f"Error creating agent {name}: {e}"

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
