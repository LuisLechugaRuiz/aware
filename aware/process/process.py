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
from aware.process.process_ids import ProcessIds
from aware.process.process_info import ProcessInfo
from aware.process.process_handler import ProcessHandler
from aware.tools.tools_manager import ToolsManager
from aware.tools.tools import Tools
from aware.utils.logger.file_logger import FileLogger


class Process:
    def __init__(
        self,
        ids: ProcessIds,
    ):
        self.ids = ids
        process_info = ClientHandlers().get_process_info(process_ids=ids)
        self.name = process_info.get_name()

        # TODO: Split logger into agent/process folder!!
        self.logger = FileLogger(self.name)

        # Get process info
        self.agent_data = process_info.agent_data
        self.process_data = process_info.process_data
        self.process_communications = process_info.process_communications
        self.process_states = process_info.process_states
        self.current_state = process_info.current_state

        # Initialize tool TODO: We should register tools outside of process. On start for each user depending on the tools have access to.
        self.tools_manager = ToolsManager(process_ids=ids, logger=self.logger)
        self.tools = self._get_tools(process_info=process_info)

        self.process_handler = ProcessHandler()

    def _get_prompt_kwargs(self) -> Dict[str, Any]:
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
        
    def _get_function_schemas(self) -> List[Dict[str, Any]]:
        function_schemas = []
        # TODO: Get from out current_state.tools filter instead of get_tools.
        for function in self.tools.get_tools():
            function_schemas.append(PydanticParser.get_function_schema(function))
        function_schemas.extend(self.process_communications.get_function_schemas())
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

            # 3. Get new requests, topic updates and function_calls
            if tool_calls:
                self.logger.info("Getting function calls.")
                self.process_tool_calls(tool_calls=tool_calls)
            else:
                self.logger.info("No tool call available.")

            # 4. In case agent scheduled a sync request don't step anymore.
            # TODO: Modify this based on the decision at process_tool_calls after create_request.
            if self.is_sync_request_scheduled():
                self.logger.info(f"Sync request scheduled, waiting for response.")
                return

            # 5. Step process.
            process_handler.step(
                process_ids=self.ids,
                is_process_finished=self.is_process_finished(),
            )
        except Exception as e:
            self.logger.error(f"Error in process_response: {e}")

    def process_tool_calls(self, tool_calls: List[ChatCompletionMessageToolCall]):
        for tool_call in tool_calls:
            service_id = self.process_communications.get_client_service_id(service_name=tool_call.function.name)
            topic_id = self.process_communications.get_publisher_topic_id(topic_name=tool_call.function.name)

            if service_id is not None:
                # TODO: Get request_message from tool_call.function.arguments!! translate into Dict[str, Any]
                # TODO: Get is_async, how should we do it? Should we add is_async as last arg to all requests?
                # Create request getting service_id from the dict.
                self.create_request(
                    function_call_id=tool_call.id,
                    service_id=service_id,
                    request_message=#TODO,
                    is_async=#TODO,
                )
                # TODO: determine what happens in case of:
                # - Function is request sync.
                # - Another future function is a tool_call, should we wait until request?
                pass
            elif topic_id is not None:
                # Update topic using topic_id from the dict.
                pass
            else:
                function_call = self.tools_manager.get_function_call(tool_call, self.tools.get_tools())
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

    # TODO: This function should be called doing a translation at post model function call to specific request, accessing the right client.
    def create_request(
        self,
        function_call_id: str,
        service_id: str,
        request_message: Dict[str, Any],
        is_async: bool,
    ):
        # - Save request in database
        result = ClientHandlers().create_request(
            user_id=self.ids.user_id,
            client_process_id=self.ids.process_id,
            client_process_name=self.name,
            service_id=service_id,
            request_message=request_message,
            is_async=is_async,
        )
        if result.error:
            error = f"Error creating request: {result.error}"
            request_error_response = ToolResponseMessage(
                content=error, tool_call_id=function_call_id
            )
            self.process_handler.add_message(
                process_ids=self.ids, message=request_error_response
            )
            return

        request = result.data
        if is_async:
            acknowledge = f"Request {request.id} created successfully"
            request_ack_response = ToolResponseMessage(
                content=acknowledge, tool_call_id=function_call_id
            )
            self.process_handler.add_message(
                process_ids=self.ids, message=request_ack_response
            )

        self.process_handler.process_request(request)

        # - Start the service process if not running
        request = result.data
        service_process_ids = ClientHandlers().get_process_ids(
            process_id=request.service_process_id
        )
        self.process_handler.start(service_process_ids)
        return f"Request {request.id} created successfully"
