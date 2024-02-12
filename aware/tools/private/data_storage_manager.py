from aware.process.process_info import ProcessInfo
from aware.tools.tools import Tools


class DataStorageManager(Tools):
    def __init__(
        self,
        process_info: ProcessInfo,
    ):
        super().__init__(process_info=process_info)

    def set_tools(self):
        return [
            # self.append_profile,
            # self.edit_profile,
            self.store,
            self.stop,
        ]

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
        return self.memory_manager.store_data(
            data=data, potential_query=potential_query
        )

    def stop(self, new_context: str):
        """Stop saving info. Call this function after all relevant data has been stored and provide a new context that overrides the previous one with the new information.

        Args:
            new_context (str): The new context to be set.
        """
        self.logger.info("Stopping data storage.")

        self.agent_data.context = new_context
        self.update_agent_data()

        self.finish_process()
        return "Context updated, agent stopped."
