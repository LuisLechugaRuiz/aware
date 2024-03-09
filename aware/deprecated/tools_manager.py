import json
import inspect
from typing import Callable, List, Optional, Type
from openai.types.chat import ChatCompletionMessageToolCall

from aware.chat.conversation_schemas import ToolResponseMessage
from aware.process.process_ids import ProcessIds
from aware.utils.logger.process_loger import ProcessLogger
from aware.tool.tools import FunctionCall, Tools
from aware.tool.tools_registry import ToolsRegistry


# TODO: Refactor. Tools should be obtained from specific capability.
class ToolsManager:
    def __init__(self, process_ids: ProcessIds, process_logger: ProcessLogger):
        self.module_path = "aware.tools.tools"
        self.tools_registry = ToolsRegistry(
            process_ids=process_ids, tools_folders=["core", "private", "public"]
        )
        self.default_tools = []
        self.logger = process_logger.get_logger("tools_manager")
        self.process_ids = process_ids

    def clean_tool_call(
        self, tool_call: ChatCompletionMessageToolCall
    ) -> ChatCompletionMessageToolCall:
        """Clean the tool call to replace any '.' in the name with ' _'."""
        tool_call.function.name = tool_call.function.name.replace(".", "_")
        return tool_call

    def get_tools(self, name: str) -> Optional[Type[Tools]]:
        self.logger.info(f"Getting tools for name: {name}")
        return self.tools_registry.get_tools(name)

    def get_function_call(
        self,
        tool_call: ChatCompletionMessageToolCall,
        functions: List[Callable],
    ) -> Optional[FunctionCall]:
        tool_call = self.clean_tool_call(tool_call)

        functions_dict = {}
        for function in functions:
            functions_dict[function.__name__] = function

        try:
            function_name = tool_call.function.name
            function = functions_dict[function_name]

            signature = inspect.signature(function)
            args = [param.name for param in signature.parameters.values()]

            arguments = json.loads(tool_call.function.arguments)

            call_arguments_dict = {}
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
            function_call = FunctionCall(
                name=function_name,
                call_id=tool_call.id,
                arguments=call_arguments_dict,
            )
            return function_call
            # args_string = "\n".join(
            #     [f"{key}={value!r}" for key, value in call_arguments_dict.items()]
            # )
            # self.logger.info(f"Function: {function.__name__}\n{args_string}")
        except Exception as e:
            self.logger.error(
                f"Error while retrieving signature for function {function_name} with arguments {call_arguments_dict}. Error: {e}"
            )
            return None

    def execute_tool(
        self, function_call: FunctionCall, functions: List[Callable]
    ) -> ToolResponseMessage:
        functions_dict = {}
        for function in functions:
            functions_dict[function.__name__] = function

        try:
            function = functions_dict[function_call.name]
            response = function(**function_call.arguments)
            args_string = "\n".join(
                [f"{key}={value!r}" for key, value in function_call.arguments.items()]
            )
            self.logger.info(
                f"Function: {function.__name__}\n{args_string}\nResponse: {response}"
            )
        except Exception as e:
            response = f"Error while executing function {function_call.name} with arguments {function_call.arguments}. Error: {e}"
            self.logger.error(response)
        finally:
            return ToolResponseMessage(
                content=response, tool_call_id=function_call.call_id
            )

    # def save_tool(self, function, name):
    #     path = os.path.join(self.tools_folder / f"{name}.py")
    #     with open(path, "w") as f:
    #         f.write(function)
