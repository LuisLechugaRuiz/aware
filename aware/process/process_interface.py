from abc import abstractmethod
from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageToolCall
from typing import Any, Dict, List

from aware.chat.chat import Chat
from aware.chat.conversation_schemas import (
    AssistantMessage,
    ToolCalls,
    ToolResponseMessage,
)
from aware.process.database.process_database_handler import ProcessDatabaseHandler
from aware.process.process_ids import ProcessIds
from aware.process.process_info import ProcessInfo
from aware.process.process_handler import ProcessHandler
from aware.tool.capability.capability import Capability
from aware.tool.capability.capability_registry import CapabilityRegistry
from aware.tool.tool import Tool
from aware.tool.tool_manager import ToolManager
from aware.utils.logger.process_loger import ProcessLogger


class ProcessInterface:
    def __init__(
        self,
        ids: ProcessIds,
    ):
        self.process_ids = ids
        process_info = ProcessDatabaseHandler().get_process_info(process_ids=ids)

        self.process_logger = ProcessLogger(
            user_id=ids.user_id,
            agent_name=process_info.agent_data.name,
            process_name=self.process_data.name,
        )
        self.logger = self.process_logger.get_logger("process")

        # Get info
        self.agent_data = process_info.agent_data

        # TODO: Implement the state machine format at all processes.
        self.process_data = process_info.process_data
        self.process_states = process_info.process_states
        self.current_state = process_info.current_state

        # Initialize tool
        self.tool_manager = ToolManager(process_logger=self.process_logger)
        self.capability = self._get_capability(process_info=process_info)
        self._initialize_tools()

        self.process_handler = ProcessHandler()

    @property
    @abstractmethod
    def name(self) -> str:
        """The name property that must be implemented by derived classes."""
        pass

    @property
    def prompt_kwargs(self) -> Dict[str, Any]:
        """The prompt_kwargs property that must be implemented by derived classes."""
        return {}

    @property
    def tools(self) -> List[Tool]:
        """The tools property that can be implemented by derived classes."""
        return []

    def execute_tool(
        self, tool_call: ChatCompletionMessageToolCall
    ) -> ToolResponseMessage:
        function_call = self.tool_manager.get_function_call(tool_call=tool_call)
        if function_call.run_remote:
            # TODO: Call supabase real-time client.
            pass

        result = self.tool_manager.execute_function(function_call=function_call)
        return ToolResponseMessage(content=result, tool_call_id=tool_call.id)

    def _get_prompt_kwargs(self) -> Dict[str, Any]:
        all_prompt_kwargs = self.prompt_kwargs
        all_prompt_kwargs["name"] = self.name
        all_prompt_kwargs.update(self.current_state.to_prompt_kwargs())
        all_prompt_kwargs.update(self.agent_data.to_prompt_kwargs())
        return all_prompt_kwargs

    def _get_capability(self, process_info: ProcessInfo) -> Capability:
        # TODO: DETERMINE module_path depending on the use-case!!!
        self.module_path = "aware.tools.tools"
        self.capability_registry = CapabilityRegistry(
            process_ids=self.process_ids,
            process_loger=self.process_logger,
            capabilities_folders=["core", "private", "public"],
        )

        capability_class = process_info.process_data.capability_class
        capability_class_type = self.capability_registry.get_capability(
            name=capability_class
        )

        if capability_class_type is None:
            raise Exception("Capability class not found")
        return capability_class_type(
            process_info=process_info,
        )

    def _initialize_tools(self):
        all_tools = self.tools

        tool_names = (
            self.current_state.tools.keys()
        )  # Tools is: tool_name + transition, TODO: Make it explicit.
        all_tools.extend(self.capability.get_filtered_tools(tool_names=tool_names))

        self.tool_manager.register_tools(tools=all_tools)

    def preprocess(self):
        chat = Chat(
            name=self.name,
            process_ids=self.process_ids,
            prompt_kwargs=self._get_prompt_kwargs(),
            logger=self.logger,
        )
        chat.request_response(tools_openai=self.tool_manager.get_openai_tools())

    def postprocess(self, response_str: str) -> List[ToolResponseMessage]:
        try:
            # 1. Reconstruct response.
            openai_response = ChatCompletionMessage.model_validate_json(response_str)
            tool_calls = openai_response.tool_calls
            if tool_calls is not None:
                new_message = ToolCalls.from_openai(
                    assistant_name=self.name,
                    tool_calls=openai_response.tool_calls,
                )
            else:
                tool_calls = [
                    self.capability.get_default_tool_call(openai_response.content)
                ]
                if tool_calls is not None:
                    new_message = ToolCalls.from_openai(
                        assistant_name=self.name,
                        tool_calls=tool_calls,
                    )
                else:
                    new_message = AssistantMessage(
                        name=self.name, content=openai_response.content
                    )

            # 2. Upload message to Supabase and Redis.
            self.logger.info("Adding message to redis and supabase")
            process_handler = ProcessHandler()
            process_handler.add_message(
                process_ids=self.process_ids, message=new_message
            )

            # 3. Process tool calls: Send Communications or Call Functions.
            if tool_calls:
                self.logger.info("Getting function calls.")
                self.process_tool_calls(tool_calls=tool_calls)

            # TODO: ADDRESS ME PROPERLY!! process_tool_calls should trigger transition and update process state. In case the transition is END we should call on_finish
            #  on_finish will help us to set_input_completed on main process and also to send this info to step()!!
            if self.process_data.status == "END":
                self.on_finish()
                is_process_finished = True
            else:
                is_process_finished = False

            # 4. Step process if needed
            self.logger.info("Stepping process.")
            self.process_handler.step(
                process_ids=self.process_ids, is_process_finished=is_process_finished
            )
        except Exception as e:
            self.logger.error(f"Error in process_response: {e}")

    def process_tool_calls(self, tool_calls: List[ChatCompletionMessageToolCall]):
        """Default function to process tool calls by using the tools from the current capability."""

        for tool_call in tool_calls:
            tool_response = self.execute_tool(tool_call=tool_call)
            self.process_handler.add_message(
                process_ids=self.process_ids, message=tool_response
            )
            self.logger.info(
                f"Executing tool: {tool_call.function.name} with response: {tool_response.content}"
            )
            # TODO: Get transition depending on tool_name and current state!

    @abstractmethod
    def on_finish(self):
        """The on_finish method that must be implemented by derived classes."""
        pass
