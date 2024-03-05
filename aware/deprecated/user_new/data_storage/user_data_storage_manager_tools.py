from aware.data.database.client_handlers import ClientHandlers
from aware.database.weaviate.memory_manager import MemoryManager
from aware.system.data_storage_manager.data_storage_manager_tools import (
    DataStorageManagerTools,
)
from aware.utils.logger.file_logger import FileLogger


class UserDataStorageTools(DataStorageManagerTools):
    def __init__(self, user_id: str, process_id: str):
        super().__init__(user_id=user_id, process_id=process_id)
        self.logger = FileLogger("user_data_storage_manager")

    def get_tools(self):
        return [
            self.append_user_profile,
            self.edit_user_profile,
            self.store,
            self.stop,
        ]

    def append_user_profile(self, field: str, data: str):
        """
        Append data into a specific field of the user profile.

        Args:
            field (str): Field to edit.
            data (str): Data to be inserted.
        """
        supabase_handler = ClientHandlers().get_supabase_handler()
        user_profile = supabase_handler.get_user_profile(user_id=self.user_id)
        if user_profile is None:
            return "Error!! User profile not found in Supabase."
        if user_profile.get(field, None) is None:
            return f"Field {field} does not exist in user profile."
        user_profile[field] += data
        supabase_handler.update_user_profile(user_id=self.user_id, profile=user_profile)

        return "Data appended successfully."

    def edit_user_profile(self, field: str, old_data: str, new_data: str):
        """
        Edit the user profile overwriting the old data with the new data.

        Args:
            field (str): Field to edit.
            old_data (str): Old data to be replaced.
            new_data (str): New data to replace the old data.
        """
        supabase_handler = ClientHandlers().get_supabase_handler()
        user_profile = supabase_handler.get_user_profile(user_id=self.user_id)
        if user_profile is None:
            return "Error!! User profile not found in Supabase."
        current_data = user_profile.get(field, None)
        if current_data is None:
            return f"Field {field} does not exist in user profile."
        user_profile[field] = current_data.replace(old_data, new_data)
        supabase_handler.update_user_profile(user_id=self.user_id, profile=user_profile)

        return "Data edited successfully."

    def stop(self, conversation_summary: str, potential_query: str):
        """Stop saving info. Call this function after all relevant data has been stored and provide a summary of the conversation.

        Args:
            conversation_summary (str): A summary of the conversation.
            potential_query (str): A potential query that might be used to find this conversation.
        """
        memory_manager = MemoryManager(
            user_id=self.user_id,
            logger=FileLogger("user_data_storage_manager"),
        )

        memory_manager.store_conversation(
            summary=conversation_summary, potential_query=potential_query
        )
        # TODO: SHOULD WE ALSO OVERRIDE CURRENT CONTEXT BY THE SUMMARY?
        return super().stop()
