from abc import ABC
from openai.types.chat import ChatCompletionMessageToolCall
from typing import Dict, List, Optional


from aware.chat.chat import Chat
from aware.chat.conversation_schemas import ToolResponseMessage
from aware.data.database.client_handlers import ClientHandlers
from aware.tools.tools_manager import ToolsManager
from aware.tools.tools import FunctionCall, Tools
from aware.utils.logger.file_logger import FileLogger
from aware.process.process_data import ProcessData
from aware.process.decorators import on_preprocess, on_postprocess


class Process(ABC):
    process_data: ProcessData
    tools_manager: ToolsManager
    tools: Tools

    # Preprocess
    chat: Optional[Chat] = None
    initialized_for_preprocessing: bool = False
    # Postprocess
    initialized_for_postprocessing: bool = False

    def __init__(
        self,
        process_data: ProcessData,
    ):
        self.client_handlers = ClientHandlers()
        self.process_data = process_data
        self.tools_manager = ToolsManager(self.get_logger())
        self.tools = self._get_tools(process_data=process_data)

    def _get_tools(self, process_data: ProcessData) -> Tools:
        tools_class = self.client_handlers.get_tools_class(
            process_id=process_data.ids.process_id
        )
        tools_class_type = self.tools_manager.get_tools(name=tools_class)
        if tools_class_type is None:
            raise Exception("Tools class not found")
        return tools_class_type(
            client_handlers=self.client_handlers,
            process_data=process_data,
        )

    def preprocess(
        self,
    ):
        prompt_kwargs = self.process_data.get_prompt_kwargs()
        meta_prompt_kwargs = self.process_data.get_meta_prompt_kwargs()

        self.chat = Chat(
            process_ids=self.process_data.ids,
            process_name=self.get_process_name(),
            agent_name=self.process_data.agent_data.name,
            module_name=self.process_data.prompt_data.module_name,
            prompt_name=self.process_data.prompt_data.prompt_name,
            logger=self.get_logger(),
            prompt_kwargs=prompt_kwargs,
            meta_prompt_kwargs=meta_prompt_kwargs,
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

    def is_running(self) -> bool:
        return self.tools.is_running()

    @on_preprocess
    def request_response(self):
        self.chat.request_response(self.tools.get_tools())

    def should_run_remote(self) -> bool:
        return self.tools.run_remote

    def stop_agent(self):
        self.tools.stop_agent()
