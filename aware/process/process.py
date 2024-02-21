from openai.types.chat import ChatCompletionMessageToolCall
from typing import Any, Dict, List, Optional

from aware.chat.chat import Chat
from aware.chat.conversation_schemas import ToolResponseMessage
from aware.data.database.client_handlers import ClientHandlers
from aware.process.process_ids import ProcessIds
from aware.process.process_info import ProcessInfo
from aware.tools.tools_manager import ToolsManager
from aware.tools.tools import FunctionCall, Tools
from aware.utils.logger.file_logger import FileLogger


class Process:
    def __init__(
        self,
        ids: ProcessIds,
    ):
        self.ids = ids
        process_info = ClientHandlers().get_process_info(process_ids=ids)
        self.name = process_info.get_name()

        # Get process info
        self.agent_data = process_info.agent_data
        self.process_data = process_info.process_data
        self.process_communications = process_info.process_communications
        self.process_states = process_info.process_states
        self.current_state = process_info.current_state

        # Initialize tool
        self.tools_manager = ToolsManager(self.get_logger())
        self.tools = self._get_tools(process_info=process_info)

    def get_prompt_kwargs(self) -> Dict[str, Any]:
        prompt_kwargs = {"name": self.name}
        prompt_kwargs.update(self.current_state.to_prompt_kwargs())
        prompt_kwargs.update(self.process_communications.to_prompt_kwargs())
        prompt_kwargs.update(self.agent_data.to_prompt_kwargs())
        return prompt_kwargs

    def _get_tools(self, process_info: ProcessInfo) -> Tools:
        tools_class = process_info.process_data.tools_class
        tools_class_type = self.tools_manager.get_tools(name=tools_class)

        # self.current_state.tools -> TODO: Filter by all tools and get only the available ones for current state.

        if tools_class_type is None:
            raise Exception("Tools class not found")
        return tools_class_type(
            process_info=process_info,
        )

    def preprocess(
        self,
    ):
        prompt_kwargs = self.get_prompt_kwargs()
        chat = Chat(
            name=self.name,
            process_ids=self.ids,
            prompt_kwargs=prompt_kwargs,
            logger=self.get_logger(),
        )
        chat.request_response(self.tools.get_tools())
        return self

    def get_default_tool_call(
        self, content: str
    ) -> Optional[ChatCompletionMessageToolCall]:
        return self.tools.get_default_tool_call(content)

    # TODO: Split into user/agent/process ?
    def get_logger(self) -> FileLogger:
        return FileLogger(self.name)

    def get_function_calls(
        self, tool_calls: List[ChatCompletionMessageToolCall]
    ) -> List[FunctionCall]:
        return self.tools_manager.get_function_calls(tool_calls, self.tools.get_tools())

    def execute_tools(
        self, function_calls: List[FunctionCall]
    ) -> List[ToolResponseMessage]:
        tool_responses = self.tools_manager.execute_tools(
            function_calls, self.tools.get_tools()
        )
        return tool_responses

    def is_async_request_scheduled(self) -> bool:
        return self.tools.is_async_request_scheduled()

    def is_sync_request_scheduled(self) -> bool:
        return self.tools.is_sync_request_scheduled()

    def is_process_finished(self) -> bool:
        return self.tools.is_process_finished()

    def should_run_remote(self) -> bool:
        return self.tools.run_remote

    def finish_process(self):
        self.tools.finish_process()
