from abc import ABC, abstractmethod
from typing import List, Optional

from openai.types.chat import ChatCompletionMessageToolCall

from aware.agent.tools import FunctionCall, Tools
from aware.agent.decorators import on_preprocess, on_postprocess
from aware.chat.new_chat import Chat
from aware.chat.new_conversation_schemas import ToolResponseMessage
from aware.tools.tools_manager import ToolsManager
from aware.utils.logger.file_logger import FileLogger


class Process(ABC):
    user_id: str
    chat_id: str
    tools: Tools
    process_name: str
    # Preprocess
    chat: Optional[Chat] = None
    initialized_for_preprocessing: bool = False
    # Postprocess
    tools_manager: Optional[ToolsManager] = None
    initialized_for_postprocessing: bool = False

    def __init__(self, user_id: str, chat_id: str, run_remote: bool, tools: Tools):
        self.user_id = user_id
        self.chat_id = chat_id
        self.run_remote = run_remote
        self.tools = tools

    def preprocess(
        self,
    ):
        self.chat = Chat(
            process_name=self.get_process_name(),
            user_id=self.user_id,
            chat_id=self.chat_id,
            logger=self.get_logger(),
        )
        self.initialized_for_preprocessing = True
        return self

    def postprocess(self):
        self.tools_manager = ToolsManager(self.get_logger())
        self.initialized_for_postprocessing = True
        return self

    def get_default_tool_call(
        self, content: str
    ) -> Optional[ChatCompletionMessageToolCall]:
        return self.tools.get_default_tool_call(content)

    @classmethod
    @abstractmethod
    def get_process_name(self) -> str:
        pass

    @classmethod
    def get_logger(cls) -> FileLogger:
        return FileLogger(cls.get_process_name())

    @on_preprocess
    def request_response(self):
        self.chat.request_response(self.tools.get_tools())

    # TODO: Implement a decorator to mark as default tool calls?
    @on_postprocess
    def get_function_calls(
        self, tool_calls: List[ChatCompletionMessageToolCall]
    ) -> List[FunctionCall]:
        return self.tools_manager.get_function_calls(tool_calls, self.tools.get_tools())

    @on_postprocess
    def execute_tools(
        self, function_calls: List[FunctionCall]
    ) -> List[ToolResponseMessage]:
        tool_responses = self.tools_manager.execute_tools(
            function_calls, self.tools.get_tools()
        )
        return tool_responses

    def stop_agent(self):
        self.tools.stop_agent()
