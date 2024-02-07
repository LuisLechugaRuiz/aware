from typing import List
from aware.tools.tools import Tools
from aware.process.process_ids import ProcessIds
from aware.requests.service import ServiceData


class Orchestrator(Tools):
    """As orchestrator your role is to manage the task distribution within the system. For this you can create new agents or create new requests for existing ones"""

    def __init__(self, process_ids: ProcessIds):
        super().__init__(process_ids=process_ids)

    def get_tools(self):
        return [
            self.create_agent,
            self.create_request,
            self.find_agent,
            self.find_tools,
        ]

    @classmethod
    def get_services(self) -> List[ServiceData]:
        return [
            ServiceData(
                name="orchestrate",
                description="Orchestrate the agents to solve complex tasks.",
                prompt_prefix="Received the following task:",
            )
        ]

    def create_agent(self, tools: str, name: str, task: str, instructions: str):
        """
        Use this tool to create a new agent in case none of the existent ones can fulfill the step to complete the task.
        Select tools only from the existing ones retrieved using find_tools.

        params:
         name (str): Agent's name, a specific variable name used to describe the agent, will be used to identify the agent. Should follow convention: lower followed by "_".
         task (str): Agent's task, a highlevel description of his mission, should be general to solve similar requests.
         tools (str): The tools that the agent should use to accomplish the next step.
         instructions (str): Specific instructions or recommendations about possible combinations of tool executions that could be performed to satisfy the requests.
        """
        try:
            self.client_handlers.create_agent(
                user_id=self.process_data.ids.user_id,
                name=name,
                task=task,
                tools_class=tools,
                instructions=instructions,
            )
            return f"Agent {name} created successfully"
        except Exception as e:
            return f"Error creating agent {name}: {e}"

    def create_request(self, agent_name: str, request_details: str):
        """
        Create a new request that should be accomplished by an existing agent.
        Select an agent only from the existing ones retrieved using find_agent.

        params:
         agent_name (str): Agent's name matching one of the retrieved ones.
         request_details (str): A very detailed description about the request that the agent should pursue and some validations that it should verify before providing a final response.
        """

        return super().create_request(
            agent_name=agent_name, request_details=request_details
        )

    # TODO: Should we add edit_agent?

    def find_agent(self, task: str, potential_name: str):
        """
        Search an agent that could by task or potential name.

        params:
         task (str): The task that the agent could be doing, will be used to perform similarity search by cosine similarity with the agent tasks.
         potential_name (str): A specific name that the agent could have. Following convention: low letter followed by "_" (snake case?)
        """

    def find_tools(self, description: str):
        """
        Search for existing tools that can be used by the agents.

        params:
         description (str): The potential description of the existing tools.
        """