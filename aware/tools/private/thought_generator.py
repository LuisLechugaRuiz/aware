from typing import List

from aware.memory.memory_manager import MemoryManager
from aware.process.process_data import ProcessData
from aware.requests.service import ServiceData
from aware.tools.decorators import default_function
from aware.tools.tools import Tools
from aware.utils.logger.file_logger import FileLogger


class ThoughtGenerator(Tools):
    def __init__(
        self,
        process_data: ProcessData,
    ):
        super().__init__(process_data)

    def set_tools(self):
        return [
            self.intermediate_thought,
            self.final_thought,
            self.search,
        ]

    @classmethod
    def get_services(self) -> List[ServiceData]:
        return [
            ServiceData(
                name="search",
                description="Search for an answer on semantic database.",
                prompt_prefix="Received the following question:",
            )
        ]

    @classmethod
    def get_process_name(self):
        return "thought_generator"

    def search(self, questions: List[str]):
        """Search for the answer to the questions in the memory.

        Args:
            questions (List[str]): The questions to be answered.
        """
        memory_manager = MemoryManager(
            user_id=self.process_data.ids.user_id,
            logger=FileLogger("user_memory_manager", should_print=False),
        )

        return memory_manager.search_data(queries=questions)

    def intermediate_thought(self, thought: str):
        """Generate an intermediate thought that will be used to reason about the data.

        Args:
            thought (str): The thought to be processed.
        """
        self.update_thought(thought)
        return "Intermediate thought saved."

    @default_function
    def final_thought(self, thought: str):
        """Generate a final thought that will be used by the agent to optimize his performance.

        Args:
            thought (str): The thought to be processed.
        """
        self.update_thought(thought)
        self.stop_agent()
        return "Final thought saved, stopping agent."

    def update_thought(self, thought: str):
        self.process_data.agent_data.thought = thought
        self.update_agent_data()
