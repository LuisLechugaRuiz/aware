from typing import Optional

from aware.data.database.client_handlers import ClientHandlers
from aware.memory.memory_manager import MemoryManager
from aware.utils.logger.file_logger import FileLogger
from aware.tools.profile import Profile
from aware.tools.tools import Tools


class DataStorageManager(Tools):
    def __init__(self, user_id: str, agent_id: str, process_id: str):
        self.logger = FileLogger("data_storage_manager")
        super().__init__(user_id, agent_id, process_id, run_remote=False)

    def get_tools(self):
        return [
            self.append_profile,
            self.edit_profile,
            self.store,
            self.stop,
        ]

    @classmethod
    def get_process_name(self):
        return "data_storage_manager"

    def _get_agent_profile(self) -> Optional[Profile]:
        """Get the agent's profile."""
        supabase_handler = ClientHandlers().get_supabase_handler()
        agent_profile = supabase_handler.get_agent_profile(agent_id=self.agent_id)
        if agent_profile is None:
            return None
        return agent_profile

    def _update_profile(self, profile: Profile):
        supabase_handler = ClientHandlers().get_supabase_handler()
        supabase_handler.update_agent_profile(agent_id=self.agent_id, data=profile)

    def append_profile(self, field: str, data: str):
        """
        Append data into a specific field of the profile.

        Args:
            field (str): Field to edit.
            data (str): Data to be inserted.
        """
        agent_profile = self._get_agent_profile()
        if agent_profile is None:
            return "Error!! Profile not found in Supabase."
        result = agent_profile.append_profile(field=field, data=data)
        self._update_profile(agent_profile)
        return result

    def edit_profile(self, field: str, old_data: str, new_data: str):
        """
        Edit the profile overwriting the old data with the new data.

        Args:
            field (str): Field to edit.
            old_data (str): Old data to be replaced.
            new_data (str): New data to replace the old data.
        """
        agent_profile = self._get_agent_profile()
        if agent_profile is None:
            return "Error!! Profile not found in Supabase."
        result = agent_profile.edit_profile(
            field=field, old_data=old_data, new_data=new_data
        )
        self._update_profile(agent_profile)
        return result

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

    # TODO: What if we make this to store the summary based on context and we avoid having another process? (context_manager).
    # This means we just need three: Main (Always) - Thought (Always - On parallel) - Data Storage (Only when conversation buffer).
    def stop(self):
        """Stop saving info. Call this function after all relevant data has been stored."""
        logger = FileLogger("migration_tests")
        logger.info("Stopping data storage.")
        self.stop_agent()
        return "Stopped storing data."
