from typing import Optional

from aware.agent.agent_data import AgentData
from aware.data.database.client_handlers import ClientHandlers
from aware.process.process_ids import ProcessIds
from aware.requests.request import Request
from aware.tools.tools import Tools
from aware.utils.logger.file_logger import FileLogger


class ContextManager(Tools):
    def __init__(
        self,
        client_handlers: "ClientHandlers",
        process_ids: ProcessIds,
        agent_data: AgentData,
        request: Optional[Request],
        run_remote: bool = False,
    ):
        super().__init__(
            client_handlers=client_handlers,
            process_ids=process_ids,
            agent_data=agent_data,
            request=request,
            run_remote=run_remote,
        )
        self.logger = FileLogger("context_manager")

    def set_tools(self):
        return [
            self.append_context,
            self.edit_context,
        ]

    def _update_context(self, context: str):
        self.agent_data.context = context
        self.update_agent_data()

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
