import json
import inspect
from typing import Callable, List, Optional, Type
from openai.types.chat import ChatCompletionMessageToolCall

from aware.chat.conversation_schemas import ToolResponseMessage
from aware.utils.logger.file_logger import FileLogger
from aware.tools.tools import FunctionCall, Tools
from aware.tools.tools_registry import ToolsRegistry


class ToolsManager:
    def __init__(self, logger: FileLogger):
        self.module_path = "aware.tools.tools"
        self.tools_registry = ToolsRegistry(["core", "private", "public"])
        self.default_tools = []
        self.logger = logger

    def clean_tool_calls(self, tool_calls: List[ChatCompletionMessageToolCall]):
        """Clean the tool calls to replace any '.' in the name with ' _'."""
        for tool_call in tool_calls:
            tool_call.function.name = tool_call.function.name.replace(".", "_")
        return tool_calls

    def get_tools(self, name: str) -> Optional[Type[Tools]]:
        self.logger.info(f"Getting tools for name: {name}")
        return self.tools_registry.get_tools(name)

    def get_function_calls(
        self,
        tool_calls: List[ChatCompletionMessageToolCall],
        functions: List[Callable],
    ) -> List[FunctionCall]:
        tool_calls = self.clean_tool_calls(tool_calls)

        functions_dict = {}
        for function in functions:
            functions_dict[function.__name__] = function

        function_calls: List[FunctionCall] = []
        for tool_call in tool_calls:
            call_arguments_dict = {}
            try:
                function_name = tool_call.function.name
                function = functions_dict[function_name]

                signature = inspect.signature(function)
                args = [param.name for param in signature.parameters.values()]

                arguments = json.loads(tool_call.function.arguments)

                for arg in args:
                    # Check if the argument has a default value
                    default_value = signature.parameters[arg].default
                    arg_value = arguments.get(arg, None)
                    if arg_value is None and default_value is inspect.Parameter.empty:
                        raise Exception(
                            f"Function {function_name} requires argument: '{arg}' but it is not provided."
                        )
                    # Use the provided value or the default value
                    call_arguments_dict[arg] = (
                        arg_value if arg_value is not None else default_value
                    )
                function_calls.append(
                    FunctionCall(
                        name=function_name,
                        call_id=tool_call.id,
                        arguments=call_arguments_dict,
                    )
                )
                # args_string = "\n".join(
                #     [f"{key}={value!r}" for key, value in call_arguments_dict.items()]
                # )
                # self.logger.info(f"Function: {function.__name__}\n{args_string}")
            except Exception as e:
                self.logger.error(
                    f"Error while retrieving signature for function {function_name} with arguments {call_arguments_dict}. Error: {e}"
                )
        return function_calls

    def execute_tools(
        self, function_calls: List[FunctionCall], functions: List[Callable]
    ) -> List[ToolResponseMessage]:
        functions_dict = {}
        for function in functions:
            functions_dict[function.__name__] = function

        tool_response_messages = []
        for function_call in function_calls:
            try:
                function = functions_dict[function_call.name]
                response = function(**function_call.arguments)
                args_string = "\n".join(
                    [
                        f"{key}={value!r}"
                        for key, value in function_call.arguments.items()
                    ]
                )
                self.logger.info(
                    f"Function: {function.__name__}\n{args_string}\nResponse: {response}"
                )
            except Exception as e:
                response = f"Error while executing function {function_call.name} with arguments {function_call.arguments}. Error: {e}"
                self.logger.error(response)
            finally:
                tool_response_messages.append(
                    ToolResponseMessage(
                        content=response, tool_call_id=function_call.call_id
                    )
                )

        return tool_response_messages

    # def save_tool(self, function, name):
    #     path = os.path.join(self.tools_folder / f"{name}.py")
    #     with open(path, "w") as f:
    #         f.write(function)
