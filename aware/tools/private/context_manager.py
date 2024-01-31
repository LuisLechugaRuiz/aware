from aware.process.process_data import ProcessData
from aware.utils.logger.file_logger import FileLogger
from aware.tools.tools import Tools


class ContextManager(Tools):
    def __init__(
        self,
        process_data: ProcessData,
    ):
        super().__init__(process_data)
        self.logger = FileLogger("context_manager")

    def set_tools(self):
        return [
            self.append_context,
            self.edit_context,
        ]

    def _update_context(self, context):
        self.process_data.agent.context = context
        self.update_agent()

    @classmethod
    def get_process_name(self):
        return "context_manager"

    def append_context(self, data: str):
        """
        Append data at the end of the agent's context.

        Args:
            data (str): Data to be appended.
        """

        context = self.process_data.agent_data.context
        context += data
        self._update_context(context)
        self.stop_agent()
        return "Context appended."

    def edit_context(self, old_data: str, new_data: str):
        """
        Edit the agent's context overwriting the old context with the new context.

        Args:
            old_data (str): Old data that should be replaced.
            new_data (str): New data to replace the old data.
        """
        context = self.process_data.agent_data.context
        if old_data in context:
            context.replace(old_data, new_data)
            self._update_context(context)
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
