from typing import Dict, List, Optional, TYPE_CHECKING

from aware.agent.agent_builder import AgentBuilder
from aware.agent.agent_data import AgentData
from aware.communications.requests.request import Request
from aware.memory.memory_manager import MemoryManager
from aware.process.process_ids import ProcessIds
from aware.tools.tools import Tools
from aware.utils.logger.file_logger import FileLogger

if TYPE_CHECKING:
    from aware.data.database.client_handlers import ClientHandlers

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
        self.memory_manager = MemoryManager(
            user_id=self.process_ids.user_id, logger=self.logger
        )
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

    def create_agent(
        self, name: str, tools: str, identity: str, task: str, instructions: str
    ):
        """
        Use this tool to create a new agent in case none of the existent ones can fulfill the step to complete the task.
        Select tools only from the existing ones retrieved using find_tools.

        Args:
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

    def create_request(
        self, agent_name: str, request_details: str, is_async: bool = False
    ):
        """
        Create a new request that should be accomplished by an existing agent.
        Select an agent only from the existing ones retrieved using find_agent.

        Args:
            agent_name (str): Agent's name matching one of the retrieved ones.
            request_details (str): A very detailed description about the request that the agent should pursue and some validations that it should verify before providing a final response.
            is_async (bool): If the request should be performed asynchronously or not.
        """

        # TODO: Solve this as we need to send EXTERNAL request - To other agent, split between internal and external, don't assume service_name = agent_name.
        if is_async:
            return super().create_async_request(
                service_name=agent_name, request_details=request_details
            )
        else:
            return super().create_request(
                service_name=agent_name, request_details=request_details
            )

    # TODO: Should we add edit_agent?

    # TODO: Add potential name to search by keyword?
    def find_agent(self, task: str, potential_name: str):
        """
        Search an agent that could by task or potential name.

        Args:
            task (str): The task that the agent could be doing, will be used to perform similarity search by cosine similarity with the agent tasks.
            potential_name (str): A specific name that the agent could have. Following convention: low letter followed by "_" (snake case?)
        """
        agent_descriptions = self.memory_manager.find_agents(task)
        if len(agent_descriptions) > 0:
            return "\n".join(agent_descriptions)
        return "No agents found!"

    def find_tools(self, potential_approach: str, descriptions: List[str]):
        """
        Search for existing tools that can be used by the agents.
        Use a potential_approach to describe the step that should be accomplished and a list of descriptions of the tools that could be used to solve the step.

        Args:
            potential_approach (str): The potential approach that could be used to solve the current step.
            descriptions (List[str]): The descriptions of the tools that could be used.
        """

        potential_tools: Dict[str, str] = {}
        for description in descriptions:
            tools = self.memory_manager.find_tools(description)
            for tool in tools:
                potential_tools[tool.name] = tool.description
        if not potential_tools:
            return f"No tools found for approach: {potential_approach}"
        tools_str = "\n\n".join(
            f"Tool: {name}, description: {description}"
            for name, description in potential_tools.items()
        )
        return f"Found available tools:\n{tools_str}"

    def wait(self, reason: str):
        """
        Use this tool to wait for a specific reason, specially if a request should be completed or waiting for a response from an agent.

        Args:
            reason (str): The reason for waiting.
        """
        self.finish_process()
        return "Waiting..."
