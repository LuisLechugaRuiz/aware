from abc import ABC
from openai.types.chat import ChatCompletionMessageToolCall
from typing import Dict, List, Optional


from aware.chat.chat import Chat
from aware.chat.conversation_schemas import ToolResponseMessage
from aware.data.database.client_handlers import ClientHandlers
from aware.tools.tools_manager import ToolsManager
from aware.tools.tools import FunctionCall, Tools
from aware.utils.logger.file_logger import FileLogger
from aware.process.decorators import on_preprocess, on_postprocess


class Process(ABC):
    user_id: str
    process_id: str
    tools: Tools

    # Preprocess
    chat: Optional[Chat] = None
    initialized_for_preprocessing: bool = False
    # Postprocess
    tools_manager: Optional[ToolsManager] = None
    initialized_for_postprocessing: bool = False

    # TODO: Tools should be fetched from the database, based on process_id.
    def __init__(
        self,
        user_id: str,
        process_id: str,
    ):
        self.user_id = user_id
        self.process_id = process_id
        self.tools = ClientHandlers().get_tools(user_id, process_id)

    def preprocess(
        self,
        module_name: str = "system",
        prompt_name: str = "agent",
        agent_name: Optional[str] = None,
        extra_kwargs: Optional[Dict[str, str]] = None,
    ):
        self.chat = Chat(
            user_id=self.user_id,
            process_id=self.process_id,
            process_name=self.get_process_name(),
            module_name=module_name,
            prompt_name=prompt_name,
            logger=self.get_logger(),
            agent_name=agent_name,
            extra_kwargs=extra_kwargs,
        )
        self.initialized_for_preprocessing = True
        self.request_response()
        return self

    def postprocess(self):
        self.tools_manager = ToolsManager(self.get_logger())
        self.initialized_for_postprocessing = True
        return self

    def get_default_tool_call(
        self, content: str
    ) -> Optional[ChatCompletionMessageToolCall]:
        return self.tools.get_default_tool_call(content)

    def get_logger(self) -> FileLogger:
        return FileLogger(self.get_process_name())

    def get_process_name(self) -> str:
        return self.tools.__class__.__name__

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
