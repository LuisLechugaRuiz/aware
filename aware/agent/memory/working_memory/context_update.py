from aware.agent.agent import Agent
from aware.chat.chat import Chat
from aware.utils.logger.file_logger import FileLogger

DEF_DEFAULT_EMPTY_CONTEXT = "No context yet, please update it."


class ContextUpdate(Agent):
    def __init__(self, chat, initial_context: str):
        self.functions = [
            self.append_context,
            self.edit_context,
        ]
        self.context = initial_context

        super().__init__(chat=chat, functions=self.functions, logger=self.logger)

    def append_context(self, data: str):
        """
        Append data at the end of the agent's context.

        Args:
            data (str): Data to be appended.
        """
        if self.context == DEF_DEFAULT_EMPTY_CONTEXT:
            self.context = ""
        # TODO: Make this thread safe.
        self.context += data
        self.stop_agent()
        return "Context appended."

    def edit_context(self, old_data: str, new_data: str):
        """
        Edit the agent's context overwriting the old context with the new context.

        Args:
            old_data (str): Old data that should be replaced.
            new_data (str): New data to replace the old data.
        """
        # TODO: Make this thread safe.
        try:
            self.context.replace(old_data, new_data)
            self.stop_agent()
            return "Context edited."
        except Exception as e:
            return f"Error while editing context: {e}"

    def get_context(self):
        return self.context
