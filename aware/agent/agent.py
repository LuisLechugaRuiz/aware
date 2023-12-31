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
        self.running = False

    def run_agent(self, default_tool_calls: Optional[Callable] = None) -> Optional[str]:
        """Run the agent and return the message sent by the LLM in case he returns a string.

        Args:
            default_tool_calls (Optional[Callable], optional): Function to call in case the LLM returns a string. Defaults to None.
        """

        self.running = True
        while self.running:
            self.update_system()
            try:
                tool_calls = self.chat.call(functions=self.functions)
            except Exception as e:
                self.logger.error(f"Error calling chat: {e}. Stopping assistant.")
                self.running = False
                return None

            # If response is None just stop the agent.
            if tool_calls is None or not tool_calls:
                self.running = False
                print("Stopping assistant due to None call.")
                return None
            # If response is string print it and stop the agent or execute default tools call to obtain a default call.
            elif isinstance(tool_calls, str):
                if default_tool_calls is None:
                    self.chat.conversation.add_assistant_message(
                        tool_calls, assistant_name=self.chat.assistant_name
                    )
                    self.running = False
                    return tool_calls
                else:
                    tool_calls = default_tool_calls(tool_calls)
                    self.chat.conversation.add_assistant_tool_message(
                        tool_calls=tool_calls, assistant_name=self.chat.assistant_name
                    )
                    self.chat.log_conversation()
            # If response is a list of tools call them.
            try:
                self.tools_manager.execute_tools(
                    tool_calls=tool_calls,
                    functions=self.functions,
                    chat=self.chat,
                )
            except Exception as e:
                self.logger.error(f"Error executing tools: {e}. Stopping assistant.")

        return None

    def stop_agent(self):
        self.running = False

    def update_functions(self, functions: List[Callable]):
        self.functions = functions

    def update_system(self) -> str:
        """Update the system message."""
        self.chat.update_system()
