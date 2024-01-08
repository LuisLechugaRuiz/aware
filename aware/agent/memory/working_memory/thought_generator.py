import json
from openai.types.chat.chat_completion_message_tool_call_param import (
    ChatCompletionMessageToolCallParam,
    Function,
)
import threading
from typing import List
import uuid

from aware.agent.agent import Agent
from aware.agent.memory.memory_manager import MemoryManager
from aware.chat.chat import Chat
from aware.utils.logger.file_logger import FileLogger


class ThoughtGenerator(Agent):
    def __init__(
        self, chat: Chat, user_name: str, initial_thought: str, logger: FileLogger
    ):
        self.user_name = user_name
        self.functions = [
            self.intermediate_thought,
            self.final_thought,
            self.search,
        ]
        self.thought = initial_thought
        self.thought_lock = threading.Lock()
        self.memory_manager = MemoryManager(user_name=user_name, logger=logger)

        super().__init__(
            chat=chat,
            functions=self.functions,
            logger=logger,
        )

    def search(self, queries: List[str]):
        """Search the query in the manager.

        Args:
            queries (List[str]): The queries to be searched.
        """
        return self.memory_manager.search_data(queries=queries)

    def intermediate_thought(self, thought: str):
        """Generate an intermediate thought that will be used to reason about the data.

        Args:
            thought (str): The thought to be processed.
        """
        return "Intermediate thought saved."

    def final_thought(self, thought: str):
        """Generate a final thought that will be used by the agent to optimize his performance.

        Args:
            thought (str): The thought to be processed.
        """

        with self.thought_lock:
            self.thought = thought
        self.stop_agent()
        return "Final thought saved, stopping agent."

    def get_thought(self):
        with self.thought_lock:
            return self.thought

    def create_default_tool_calls(self, thought: str):
        """Create a tool call as if the agent was calling final_thought when it answer by string to avoid appending it to conversation"""
        tool_calls: List[ChatCompletionMessageToolCallParam] = [
            ChatCompletionMessageToolCallParam(
                id=uuid.uuid4(),
                function=Function(
                    arguments=json.dumps({"thought": thought}), name="final_thought"
                ),
                name="final_thought",
            )
        ]
        return tool_calls
