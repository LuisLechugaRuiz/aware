from typing import List, Optional, TYPE_CHECKING

from aware.agent.agent_data import AgentData
from aware.communications.requests.request import Request
from aware.memory.memory_manager import MemoryManager
from aware.process.process_ids import ProcessIds
from aware.process.process_handler import ProcessHandler
from aware.tools.decorators import default_function
from aware.tools.tools import Tools
from aware.utils.logger.file_logger import FileLogger

if TYPE_CHECKING:
    from aware.data.database.client_handlers import ClientHandlers

DEF_IDENTITY = """You are thought_generator, a process responsible for generating thoughts to optimize the performance of a specific agent."""
DEF_TASK = """Your task is to optimize {{ agent }}'s performance in executing its task through strategic thought generation.
{{ agent }}'s Task:
{{ agent_task }}"""
DEF_INSTRUCTIONS = """Thought Generation Steps:
1. Gather task-relevant information.
2. For complex tasks, apply intermediate_thought and refine as necessary.
3. Finalize with a strategic final_thought to guide {{ agent }}.

Operational Principles:
- Prioritize backend processing without engaging in direct interactions.
- Ensure thoughts are pertinent and flexible to the demands of {{ agent }}'s task."""


class ThoughtGenerator(Tools):
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
        self.logger = FileLogger("thought_generator")

    @classmethod
    def get_identity(cls) -> str:
        return DEF_IDENTITY

    @classmethod
    def get_task(cls, agent: str, agent_task: str) -> str:
        return DEF_TASK.format(agent=agent, agent_task=agent_task)

    @classmethod
    def get_instructions(cls) -> str:
        return DEF_INSTRUCTIONS

    def set_tools(self):
        return [
            self.intermediate_thought,
            self.final_thought,
            self.search,
        ]

    def search(self, questions: List[str]):
        """Search for the answer to the questions in the memory.

        Args:
            questions (List[str]): The questions to be answered.
        """
        memory_manager = MemoryManager(
            user_id=self.process_ids.user_id,
            logger=FileLogger("user_memory_manager", should_print=False),
        )

        return memory_manager.search_data(queries=questions)

    def intermediate_thought(self, thought: str):
        """Generate an intermediate thought that will be used to reason about the data.

        Args:
            thought (str): The thought to be processed.
        """
        return "Intermediate thought saved."

    @default_function
    def final_thought(self, thought: str):
        """Generate a final thought that will be used by the agent to optimize his performance.

        Args:
            thought (str): The thought to be processed.
        """
        self.process_handler.add_thought(process_ids=self.process_ids, thought=thought)
        self.finish_process()
        return "Final thought saved, stopping agent."
