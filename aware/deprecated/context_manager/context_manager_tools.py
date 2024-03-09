from aware.data.database.client_handlers import ClientHandlers
from aware.utils.logger.file_logger import FileLogger
from aware.tool.tools import Tools


class ContextManagerTools(Tools):
    def __init__(self, user_id: str, process_id: str):
        super().__init__(user_id=user_id, process_id=process_id)
        self.logger = FileLogger("context_manager")

    def get_tools(self):
        return [
            self.append_context,
            self.edit_context,
        ]

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

    def append_context(self, data: str):
        """
        Append data at the end of the agent's context.

        Args:
            data (str): Data to be appended.
        """

        supabase_handler = ClientHandlers().get_supabase_handler()
        context = supabase_handler.get_topic_content(
            user_id=self.user_id, name="assistant_context"
        )  # TODO: GET DEPENDING ON AGENT NAME!
        context += data
        supabase_handler.set_topic_content(
            user_id=self.user_id, name="assistant_context", content=context
        )
        self.stop_agent()
        return "Context appended."

    def edit_context(self, old_data: str, new_data: str):
        """
        Edit the agent's context overwriting the old context with the new context.

        Args:
            old_data (str): Old data that should be replaced.
            new_data (str): New data to replace the old data.
        """
        supabase_handler = ClientHandlers().get_supabase_handler()
        context = supabase_handler.get_topic_content(
            user_id=self.user_id, name="assistant_context"
        )  # TODO: GET DEPENDING ON AGENT NAME!
        if old_data in context:
            context.replace(old_data, new_data)
            supabase_handler.set_topic_content(
                user_id=self.user_id, name="assistant_context", content=context
            )
            self.stop_agent()
            return "Context edited."
        else:
            # TODO: Should we stop? I guess no as it failed.
            return "Error: Old data not found in context, please verify that it exists and you want to replace it."

    # TODO: Do we need to give this feature on first iteration? So it can remove old conversation context!
    # def clear_context(self):
    #     """
    #     Clear the agent's context, setting it to an empty string.
    #     """
    #     with self.context_lock:
    #         self.context = ""
