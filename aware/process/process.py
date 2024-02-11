from openai.types.chat import ChatCompletionMessageToolCall
from typing import List, Optional, TYPE_CHECKING

from aware.agent.agent_data import AgentData
from aware.chat.chat import Chat
from aware.chat.conversation_schemas import ToolResponseMessage
from aware.process.process_data import ProcessData
from aware.process.process_ids import ProcessIds
from aware.process.process_interface import ProcessInterface
from aware.process.process_communications import ProcessCommunications
from aware.tools.tools_manager import ToolsManager
from aware.tools.tools import FunctionCall, Tools
from aware.utils.logger.file_logger import FileLogger

if TYPE_CHECKING:
    from aware.data.database.client_handlers import ClientHandlers


class Process(ProcessInterface):
    def __init__(
        self,
        client_handlers: ClientHandlers,
        ids: ProcessIds,
        process_communications: ProcessCommunications,
        process_data: ProcessData,
        agent_data: AgentData,
    ):
        super().__init__(
            ids=ids,
            process_data=process_data,
            process_communications=process_communications,
            agent_data=agent_data,
        )

        self.client_handlers = client_handlers
        self.tools_manager = ToolsManager(self.get_logger())
        self.tools = self._get_tools()

    def _get_tools(self) -> Tools:
        tools_class = self.client_handlers.get_tools_class(
            process_id=self.ids.process_id
        )
        tools_class_type = self.tools_manager.get_tools(name=tools_class)
        if tools_class_type is None:
            raise Exception("Tools class not found")
        return tools_class_type(
            client_handlers=self.client_handlers,
            process_ids=self.ids,
            agent_data=self.agent_data,
            request=self.get_current_request(),
        )

    def preprocess(
        self,
    ):
        prompt_kwargs = self.get_prompt_kwargs()
        chat = Chat(
            client_handlers=self.client_handlers,
            process_ids=self.ids,
            process_name=self.process_data.name,
            prompt_kwargs=prompt_kwargs,
            logger=self.get_logger(),
        )
        chat.request_response(self.tools.get_tools())
        return self

    def get_default_tool_call(
        self, content: str
    ) -> Optional[ChatCompletionMessageToolCall]:
        return self.tools.get_default_tool_call(content)

    def get_logger(self) -> FileLogger:
        return FileLogger(self.process_data.name)

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
