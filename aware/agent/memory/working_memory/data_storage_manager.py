from aware.agent.agent import Agent
from typing import Callable, List

from aware.agent.memory.memory_manager import MemoryManager
from aware.chat.chat import Chat
from aware.utils.logger.file_logger import FileLogger


class DataStorageManager(Agent):
    def __init__(
        self,
        chat: Chat,
        user_name: str,
        logger: FileLogger,
        functions: List[Callable] = [],
    ):
        self.memory_manager = MemoryManager(user_name=user_name, logger=logger)
        self.default_functions = [
            self.store,
            self.stop,
        ]
        agent_functions = self.default_functions.copy()
        agent_functions.extend(functions)
        self.user_name = user_name
        super().__init__(chat=chat, functions=agent_functions, logger=logger)

    def store(self, data: str, potential_query: str):
        """
        Stores data in the Weaviate database with an associated potential query for future retrieval.

        Args:
            data (str): The data to be stored.
            potential_query (str): A related query for future data retrieval.

        Returns:
            str: Feedback message.
        """

        return self.memory_manager.store_data(
            data=data, potential_query=potential_query
        )

    def stop(self):
        """Stop saving info. Call this function after all relevant data has been stored."""
        self.stop_agent()
