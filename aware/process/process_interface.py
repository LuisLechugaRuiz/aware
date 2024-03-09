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

        # Get process info
        self.agent_data = process_info.agent_data

        # TODO: Implement the state machine format at all processes.
        self.process_data = process_info.process_data
        self.process_states = process_info.process_states
        self.current_state = process_info.current_state

        # Initialize tool
        self.capability = self._get_capability(process_info=process_info)

        self.process_handler = ProcessHandler()

    @property
    @abstractmethod
    def name(self) -> str:
        """The name property that must be implemented by derived classes."""
        pass

    @property
    @abstractmethod
    def prompt_kwargs(self) -> Dict[str, Any]:
        """The prompt_kwargs property that must be implemented by derived classes."""
        pass

    @property
    def tools_openai(self) -> List[ChatCompletionMessageToolCall]:
        """The tools_openai property that must be implemented by derived classes."""
        return []

    def execute_tool(self, tool_call: ChatCompletionMessageToolCall):
        function_call = self.capability.get_function_call(tool_call=tool_call)
        if function_call.run_remote:
            # TODO: Call supabase real-time client.
            pass

        result = self.capability.execute_tool(function_call=function_call)
        tool_response = ToolResponseMessage(content=result, tool_call_id=tool_call.id)
        self.process_handler.add_message(
            process_ids=self.process_ids, message=tool_response
        )
        self.logger.info(
            f"Executing tool: {tool_call.function.name} with response: {result}"
        )
        return function_call.should_continue

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
            process_ids=self.process_ids, tools_folders=["core", "private", "public"]
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

    def _get_openai_tools(self) -> List[ChatCompletionMessageToolCall]:
        all_openai_tools: List[ChatCompletionMessageToolCall] = self.tools_openai

        tool_names = (
            self.current_state.tools.keys()
        )  # Tools is: tool_name + transition, TODO: Make it explicit.
        openai_tools = all_openai_tools.extend(
            self.capability.get_filtered_openai_tools(tool_names=tool_names)
        )
        return openai_tools

    def preprocess(self):
        chat = Chat(
            name=self.name,
            process_ids=self.process_ids,
            prompt_kwargs=self._get_prompt_kwargs(),
            logger=self.logger,
        )
        chat.request_response(tools_openai=self._get_openai_tools())

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
                should_continue = self.process_tool_calls(tool_calls=tool_calls)

            # 4. Step process if needed.
            self.step(should_continue)
        except Exception as e:
            self.logger.error(f"Error in process_response: {e}")

    def process_tool_calls(
        self, tool_calls: List[ChatCompletionMessageToolCall]
    ) -> bool:
        """Default function to process tool calls by using the tools from the current capability."""

        should_continue = True
        for tool_call in tool_calls:
            tool_continue = self.execute_tool(tool_call=tool_call)
            if should_continue:
                should_continue = tool_continue
        return should_continue

    @abstractmethod
    def step(self, should_continue: bool):
        """The step method that must be implemented by derived classes."""
        pass
