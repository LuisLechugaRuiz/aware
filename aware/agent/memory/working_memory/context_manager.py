import threading

from aware.agent.old_agent import Agent
from aware.chat.chat import Chat
from aware.utils.json_manager import JSONManager
from aware.utils.logger.file_logger import FileLogger


class ContextManager(Agent):
    def __init__(
        self,
        chat: Chat,
        logger: FileLogger,
        json_manager: JSONManager,
    ):
        self.functions = [
            self.append_context,
            self.edit_context,
        ]
        agent_initial_functions = self.functions.copy()
        agent_initial_functions.append(self.clear_context)
        self.json_manager = json_manager
        self.initial_template = self.initialize_context()
        self.context_lock = threading.Lock()

        super().__init__(chat=chat, functions=agent_initial_functions, logger=logger)

    def append_context(self, data: str):
        """
        Append data at the end of the agent's context.

        Args:
            data (str): Data to be appended.
        """
        with self.context_lock:
            self.context += data
            self.update_context()
        self.stop_agent()
        return "Context appended."

    def clear_context(self):
        """
        Clear the agent's context, setting it to an empty string.
        """
        with self.context_lock:
            self.context = ""

    def edit_context(self, old_data: str, new_data: str):
        """
        Edit the agent's context overwriting the old context with the new context.

        Args:
            old_data (str): Old data that should be replaced.
            new_data (str): New data to replace the old data.
        """
        with self.context_lock:
            if old_data in self.context:
                self.context.replace(old_data, new_data)
                self.update_context()
                self.stop_agent()
                return "Context edited."
            else:
                return "Error: Old data not found in context, please verify that it exists and you want to replace it."

    def get_context(self):
        with self.context_lock:
            return self.context

    def initialize_context(self):
        context, date = self.json_manager.get_with_date(field="context")
        initial_template = f"From last iteration on {date} (Remove it all if not needed anymore using clear_context):\n"
        self.context = f"{initial_template}{context}"
        return initial_template

    def summarize_context(self, summary: str):
        with self.context_lock:
            self.context = summary
            self.update_context()

    def update_context(self):
        if self.initial_template:
            self.context = self.context.removeprefix(self.initial_template)
            self.initial_template = ""
            self.update_functions(
                self.functions
            )  # Remove clear_context from the functions list
        self.json_manager.update(field="context", data=self.context, logger=self.logger)
