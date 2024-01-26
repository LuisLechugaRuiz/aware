from aware.memory.memory_manager import MemoryManager
from aware.utils.logger.file_logger import FileLogger
from aware.tools.tools import Tools


class DataStorageManager(Tools):
    def __init__(self, user_id: str, process_id: str):
        self.logger = FileLogger("data_storage_manager")
        super().__init__(user_id, process_id, run_remote=False)

    def get_tools(self):
        return [
            self.store,
            self.stop,
        ]

    @classmethod
    def get_process_name(self):
        return "data_storage_manager"

    def store(self, data: str, potential_query: str):
        """
        Stores data in the Weaviate database with an associated potential query for future retrieval.

        Args:
            data (str): The data to be stored.
            potential_query (str): A related query for future data retrieval, should be a question.

        Returns:
            str: Feedback message.
        """
        memory_manager = MemoryManager(
            user_id=self.user_id,
            logger=self.logger,
        )

        return memory_manager.store_data(data=data, potential_query=potential_query)

    def stop(self):
        """Stop saving info. Call this function after all relevant data has been stored."""
        logger = FileLogger("migration_tests")
        logger.info("Stopping data storage.")
        self.stop_agent()
        return "Stopped storing data."
