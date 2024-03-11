import json
from typing import List, Optional
from openai.types.chat import ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam

from aware.chat.conversation_schemas import ToolResponseMessage
from aware.tool.helpers.function_call import FunctionCall
from aware.tool.tool import Tool
from aware.tool.tool_registry import ToolRegistry
from aware.utils.logger.process_logger import ProcessLogger


class ToolManager:
    def __init__(self, process_logger: ProcessLogger):
        self.tool_registry = ToolRegistry()
        self.logger = process_logger.get_logger("tool_manager")

    def register_tools(self, tools: List[Tool]):
        self.tool_registry.register_tools(tools)

    def clean_tool_call(
        self, tool_call: ChatCompletionMessageToolCall
    ) -> ChatCompletionMessageToolCall:
        """Clean the tool call to replace any '.' in the name with ' _'."""
        tool_call.function.name = tool_call.function.name.replace(".", "_")
        return tool_call

    # This function helps us to select the tool and use it with call_arguments_dict, TODO: Rethink name and logic with execute_tool at ProcessInterface, maybe we can remove FunctionCall.
    def get_function_call(
        self, tool_call: ChatCompletionMessageToolCall
    ) -> Optional[FunctionCall]:
        tool_call = self.clean_tool_call(tool_call)
        try:
            function_name = tool_call.function.name
            tool = self.tool_registry.get_tool(function_name)

            arguments = json.loads(tool_call.function.arguments)
            call_arguments_dict = {}

            for arg_name, (arg_type, has_default) in tool.params.items():
                arg_value = arguments.get(arg_name)

                # If arg_value is None and the parameter does not have a default value, raise an exception
                if arg_value is None and not has_default:
                    raise Exception(
                        f"Function {function_name} requires argument: '{arg_name}' but it is not provided."
                    )

                # If arg_value is provided, use it; otherwise, skip it since it must have a default value
                if arg_value is not None:
                    call_arguments_dict[arg_name] = arg_value

            function_call = FunctionCall(
                name=function_name,
                call_id=tool_call.id,
                arguments=call_arguments_dict,
                run_remote=tool.run_remote,
            )
            return function_call
        except Exception as e:
            self.logger.error(
                f"Error while retrieving signature for function {function_name} with arguments {call_arguments_dict}. Error: {e}"
            )
            return None

    def get_openai_tools(self) -> List[ChatCompletionToolParam]:
        return self.tool_registry.get_openai_tools()

    def execute_function(self, function_call: FunctionCall) -> ToolResponseMessage:
        try:
            tool = self.tool_registry.get_tool(function_call.name)
            response = tool.callback(**function_call.arguments)
            args_string = "\n".join(
                [f"{key}={value!r}" for key, value in function_call.arguments.items()]
            )
            self.logger.info(
                f"Function: {function_call.name}\n{args_string}\nResponse: {response}"
            )
        except Exception as e:
            response = f"Error while executing function {function_call.name} with arguments {function_call.arguments}. Error: {e}"
            self.logger.error(response)
        finally:
            return ToolResponseMessage(
                content=response, tool_call_id=function_call.call_id
            )
