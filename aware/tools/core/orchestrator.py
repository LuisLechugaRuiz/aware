from typing import List, Optional

from aware.agent.agent_builder import AgentBuilder
from aware.agent.agent_data import AgentData
from aware.data.database.client_handlers import ClientHandlers
from aware.process.process_ids import ProcessIds
from aware.requests.request import Request
from aware.requests.service import ServiceData
from aware.tools.tools import Tools
from aware.utils.logger.file_logger import FileLogger

DEF_IDENTITY = """You are orchestrator, an advanced virtual assistant capable of managing multiple agents to solve complex tasks"""
DEF_TASK = """Your task is to delegate atomic requests to the appropriate agents and manage the communication between them."""


class Orchestrator(Tools):
    """As orchestrator your role is to manage the task distribution within the system. For this you can create new agents or create new requests for existing ones"""

    def __init__(
        self,
        client_handlers: "ClientHandlers",
        process_ids: ProcessIds,
        agent_data: AgentData,
        request: Optional[Request],
        run_remote: bool = False,
    ):
        super().__init__(
            client_handlers=client_handlers,
            process_ids=process_ids,
            agent_data=agent_data,
            request=request,
            run_remote=run_remote,
        )
        self.agent_builder = AgentBuilder(client_handlers=self.client_handlers)
        self.logger = FileLogger("orchestrator")

    @classmethod
    def get_identity(cls) -> str:
        return DEF_IDENTITY

    @classmethod
    def get_task(cls) -> str:
        return DEF_TASK

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

    def create_agent(
        self, name: str, tools: str, identity: str, task: str, instructions: str
    ):
        """
        Use this tool to create a new agent in case none of the existent ones can fulfill the step to complete the task.
        Select tools only from the existing ones retrieved using find_tools.

        params:
         name (str): Agent's name, a specific variable name used to describe the agent, will be used to identify the agent. Should follow convention: lower followed by "_".
         tools (str): The tools that the agent should use to accomplish the next step.
         identity (str): A natural description of the agent's identity, should start with "You are {name}...".
         task (str): Agent's task, a highlevel description of his mission, should be general to solve similar requests.
         instructions (str): Specific instructions or recommendations about possible combinations of tool executions that could be performed to satisfy the requests.
        """
        try:
            self.agent_builder.create_agent(
                user_id=self.process_ids.user_id,
                name=name,
                tools_class=tools,
                identity=identity,
                task=task,
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
