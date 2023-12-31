from typing import Callable, List, Optional

from aware.chat.chat import Chat
from aware.tools.tools_manager import ToolsManager
from aware.utils.logger.file_logger import FileLogger


class Agent:
    """
    Agent that runs a loop executing tools.
    For this it uses the chat abstractions (to get model response)
    and uses tool manager to execute tools and save the results in the chat.
    """

    def __init__(
        self,
        chat: Chat,
        functions: List[Callable],
        logger: FileLogger,
    ):
        self.chat = chat
        self.tools_manager = ToolsManager(logger)
        self.functions = functions
        self.logger = logger

    def run_agent(self) -> Optional[str]:
        """Run the agent and return the message sent by the LLM in case he returns a string."""

        self.running = True
        while self.running:
            self.update_system()
            try:
                tools_call = self.chat.call(functions=self.functions)
            except Exception as e:
                self.logger.error(f"Error calling chat: {e}. Stopping assistant.")
                self.running = False
                return None

            if tools_call is None or not tools_call:
                self.running = False
                print("Stopping assistant due to None call.")
                return None
            elif isinstance(tools_call, str):
                self.running = False
                return tools_call
            else:
                try:
                    self.tools_manager.execute_tools(
                        tools_call=tools_call,
                        functions=self.functions,
                        chat=self.chat,
                    )
                except Exception as e:
                    self.logger.error(
                        f"Error executing tools: {e}. Stopping assistant."
                    )

        return None

    def stop_agent(self):
        self.running = False

    def update_functions(self, functions: List[Callable]):
        self.functions = functions

    def update_system(self) -> str:
        """Update the system message."""
        self.chat.update_system()
