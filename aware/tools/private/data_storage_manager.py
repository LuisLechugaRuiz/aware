from aware.memory.memory_manager import MemoryManager
from aware.process.process_data import ProcessData
from aware.utils.logger.file_logger import FileLogger
from aware.tools.tools import Tools


class DataStorageManager(Tools):
    def __init__(self, process_data: ProcessData):
        self.logger = FileLogger("data_storage_manager")
        super().__init__(process_data)

    def set_tools(self):
        return [
            # self.append_profile,
            # self.edit_profile,
            self.store,
            self.stop,
        ]

    @classmethod
    def get_process_name(self):
        return "data_storage_manager"

    # TODO: Temporally disabled, we need a way to manage the full profile (and fields) ensuring max tokens.
    # def append_profile(self, field: str, data: str):
    #     """
    #     Append data into a specific field of the profile.

    #     Args:
    #         field (str): Field to edit.
    #         data (str): Data to be inserted.
    #     """
    #     result = self.process_data.agent_data.profile.append_profile(
    #         field=field, data=data
    #     )
    #     self.update_agent_data()
    #     return result

    # def edit_profile(self, field: str, old_data: str, new_data: str):
    #     """
    #     Edit the profile overwriting the old data with the new data.

    #     Args:
    #         field (str): Field to edit.
    #         old_data (str): Old data to be replaced.
    #         new_data (str): New data to replace the old data.
    #     """
    #     result = self.process_data.agent_data.profile.edit_profile(
    #         field=field, old_data=old_data, new_data=new_data
    #     )
    #     self.update_agent_data()
    #     return result

    def store(self, data: str, potential_query: str):
        """
        Stores data in the Weaviate database with an associated potential query for future retrieval.

        Args:
            data (str): The data to be stored.
            potential_query (str): A related query for future data retrieval, should be a question.
        """
        memory_manager = MemoryManager(
            user_id=self.process_data.ids.user_id,
            logger=self.logger,
        )

        return memory_manager.store_data(data=data, potential_query=potential_query)

    def stop(self, new_context: str):
        """Stop saving info. Call this function after all relevant data has been stored and provide a new context that overrides the previous one with the new information.

        Args:
            new_context (str): The new context to be set.
        """
        logger = FileLogger("migration_tests")
        logger.info("Stopping data storage.")

        self.process_data.agent_data.context = new_context
        self.update_agent_data()

        self.stop_agent()
        return "Context updated, agent stopped."
