from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageToolCall
from typing import Any, Dict, List

from aware.chat.chat import Chat
from aware.chat.conversation_schemas import (
    AssistantMessage,
    ToolCalls,
    ToolResponseMessage,
)
from aware.chat.parser.pydantic_parser import PydanticParser
from aware.data.database.client_handlers import ClientHandlers
from aware.communications.communication_handler import CommunicationHandler
from aware.process.process_ids import ProcessIds
from aware.process.process_info import ProcessInfo
from aware.process.process_handler import ProcessHandler
from aware.tools.tools_manager import ToolsManager
from aware.tools.tools import Tools
from aware.utils.logger.process_loger import ProcessLogger


class Process:
    def __init__(
        self,
        ids: ProcessIds,
    ):
        self.ids = ids
        process_info = ClientHandlers().get_process_info(process_ids=ids)
        self.name = process_info.get_name()

        self.process_logger = ProcessLogger(
            user_id=ids.user_id,
            agent_name=process_info.agent_data.name,
            process_name=self.process_data.name,
        )
        self.logger = self.process_logger.get_logger("process")

        # Get process info
        self.agent_data = process_info.agent_data
        self.process_data = process_info.process_data
        self.process_states = process_info.process_states
        self.current_state = process_info.current_state

        # Initialize tool TODO: We should register tools outside of process. On start for each user depending on the tools have access to.
        self.tools_manager = ToolsManager(
            process_ids=ids, process_logger=self.process_logger
        )
        self.tools = self._get_tools(process_info=process_info)

        self.process_handler = ProcessHandler()
        self.communication_handler = CommunicationHandler(
            process_ids=self.ids,
            communications=process_info.communications,
            process_logger=self.process_logger,
        )

    def _get_prompt_kwargs(self) -> Dict[str, Any]:
        prompt_kwargs = {"name": self.name}
        prompt_kwargs.update(self.current_state.to_prompt_kwargs())
        prompt_kwargs.update(self.communication_handler.to_prompt_kwargs())
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

    def _get_function_schemas(self) -> List[Dict[str, Any]]:
        function_schemas = []
        # TODO: Get from out current_state.tools filter instead of get_tools.
        for function in self.tools.get_tools():
            function_schemas.append(PydanticParser.get_function_schema(function))
        function_schemas.extend(self.communication_handler.get_function_schemas())
        return function_schemas

    def preprocess(self):
        chat = Chat(
            name=self.name,
            process_ids=self.ids,
            prompt_kwargs=self._get_prompt_kwargs(),
            logger=self.logger,
        )
        chat.request_response(function_schemas=self._get_function_schemas())

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
                tool_calls = [self.tools.get_default_tool_call(openai_response.content)]
                if tool_calls is not None:
                    new_message = ToolCalls.from_openai(
                        assistant_name=self.name,
                        tool_calls=tool_calls,
                    )
                else:
                    new_message = AssistantMessage(
                        name=self.name, content=openai_response.content
                    )
                    self.finish_process()

            # 2. Upload message to Supabase and Redis.
            self.logger.info("Adding message to redis and supabase")
            process_handler = ProcessHandler()
            process_handler.add_message(process_ids=self.ids, message=new_message)

            # 3. Process tool calls: Send Communications or Call Functions.
            if tool_calls:
                self.logger.info("Getting function calls.")
                should_step = self.process_tool_calls(tool_calls=tool_calls)
            else:
                self.logger.info("No tool call available.")

            # 4. Step process if needed.
            if should_step:
                self.logger.info("Stepping process.")
                process_handler.step(
                    process_ids=self.ids,
                    is_process_finished=self.is_process_finished(),
                )
        except Exception as e:
            self.logger.error(f"Error in process_response: {e}")

    def process_tool_calls(
        self, tool_calls: List[ChatCompletionMessageToolCall]
    ) -> bool:
        should_step = True
        for tool_call in tool_calls:
            response = self.communication_handler.process_tool_call(
                process_name=self.name, tool_call=tool_call
            )
            if response.SYNC_REQUEST_SCHEDULED:
                # Don't step anymore, wait for response.
                # TODO: There is a corner case here, if the model executes function after scheduling a request we will execute them and then stop, maybe this is intended.
                should_step = False
            elif response.NOT_COMMUNICATION_SCHEDULED:
                function_call = self.tools_manager.get_function_call(
                    tool_call, self.tools.get_tools()
                )
                # TODO: Do this for each tool!!
                if self.should_run_remote():
                    # TODO: Call supabase real-time client.
                    pass
                else:
                    self.logger.info("Executing function call: {tool}")
                    tool_response = self.tools_manager.execute_tool(
                        function_call, self.tools.get_tools()
                    )
                    self.process_handler.add_message(
                        process_ids=self.ids, message=tool_response
                    )
        return should_step

    def is_process_finished(self) -> bool:
        return self.tools.is_process_finished()

    def should_run_remote(self) -> bool:
        return self.tools.run_remote

    def finish_process(self):
        self.tools.finish_process()
