from typing import List

from aware.data.database.client_handlers import ClientHandlers
from aware.utils.logger.file_logger import FileLogger
from aware.memory.memory_manager import MemoryManager
from aware.tools.decorators import default_function
from aware.tools.tools import Tools


class ThoughtGenerator(Tools):
    def __init__(self, user_id: str, agent_id: str, process_id: str):
        super().__init__(user_id, agent_id, process_id, run_remote=False)

    def get_tools(self):
        return [
            self.intermediate_thought,
            self.final_thought,
            self.search,
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
            user_id=self.user_id,
            logger=FileLogger("user_memory_manager", should_print=False),
        )

        return memory_manager.search_data(queries=questions)

    def intermediate_thought(self, thought: str):
        """Generate an intermediate thought that will be used to reason about the data.

        Args:
            thought (str): The thought to be processed.
        """
        self.update_thought(
            thought
        )  # TODO: This should be a publisher with the new thought!
        return "Intermediate thought saved."

    @default_function
    def final_thought(self, thought: str):
        """Generate a final thought that will be used by the agent to optimize his performance.

        Args:
            thought (str): The thought to be processed.
        """
        self.update_thought(
            thought
        )  # TODO: This should be a publisher with the new thought!
        self.stop_agent()
        return "Final thought saved, stopping agent."

    # TODO: We should add a @publishes decorator instead of calling update_thought directly.
    def update_thought(self, thought: str):
        supabase_handler = ClientHandlers().get_supabase_handler()
        supabase_handler.set_topic_content(
            user_id=self.user_id, name="assistant_thought", content=thought
        )
