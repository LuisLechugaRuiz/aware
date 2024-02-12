from typing import List

from aware.process.process_info import ProcessInfo
from aware.tools.decorators import default_function
from aware.tools.tools import Tools


class ThoughtGenerator(Tools):
    def __init__(self, process_info: ProcessInfo):
        super().__init__(process_info=process_info)

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
        return self.memory_manager.search_data(queries=questions)

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
