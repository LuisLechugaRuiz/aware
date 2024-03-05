import json
from openai.types.chat.chat_completion_message_tool_call_param import (
    ChatCompletionMessageToolCallParam,
    Function,
)
import threading
from typing import Callable, List, Optional
import uuid

from aware.deprecated.old_agent import Agent
from aware.database.weaviate.memory_manager import MemoryManager
from aware.deprecated.chat import Chat
from aware.utils.json_manager import JSONManager
from aware.utils.logger.file_logger import FileLogger


class ThoughtGenerator(Agent):
    def __init__(
        self,
        chat: Chat,
        user_name: str,
        memory_manager: MemoryManager,
        logger: FileLogger,
        json_manager: Optional[JSONManager] = None,
        functions: List[Callable] = [],
    ):
        self.user_name = user_name
        self.memory_manager = memory_manager

        self.json_manager = json_manager
        if self.json_manager is not None:
            self.thought = self.initial_thought()
        else:
            self.thought = ""
        self.thought_lock = threading.Lock()

        self.default_functions = [
            self.intermediate_thought,
            self.final_thought,
            self.search,
        ]
        agent_functions = self.default_functions.copy()
        agent_functions.extend(functions)
        super().__init__(
            chat=chat,
            functions=agent_functions,
            logger=logger,
        )

    def search(self, questions: List[str]):
        """Search for the answer to the questions in the memory.

        Args:
            questions (List[str]): The questions to be answered.
        """
        return self.memory_manager.search_data(queries=questions)

    def intermediate_thought(self, thought: str):
        """Generate an intermediate thought that will be used to reason about the data.

        Args:
            thought (str): The thought to be processed.
        """
        self.thought = thought
        self.update_thought()
        return "Intermediate thought saved."

    def final_thought(self, thought: str):
        """Generate a final thought that will be used by the agent to optimize his performance.

        Args:
            thought (str): The thought to be processed.
        """

        with self.thought_lock:
            self.thought = thought
            self.update_thought()
        self.stop_agent()
        return "Final thought saved, stopping agent."

    def get_thought(self):
        with self.thought_lock:
            return self.thought

    def initial_thought(self):
        thought, date = self.json_manager.get_with_date(field="thought")
        return f"From previous conversation on {date}:\nThought: {thought}"

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

    def update_thought(self):
        if self.json_manager is not None:
            self.json_manager.update(
                field="thought", data=self.thought, logger=self.logger
            )
