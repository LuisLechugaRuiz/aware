import glob
import json
import importlib
import inspect
from pathlib import Path
import os
import warnings
from typing import Callable, List, Optional
from openai.types.chat import ChatCompletionMessageToolCall

from aware.architecture.helpers.tool import Tool
from aware.chat.chat import Chat
from aware.utils.logger.file_logger import FileLogger


class ToolsManager:
    def __init__(self, logger: FileLogger):
        self.module_path = "aware.tools.tools"
        self.tools_folder = Path(__file__).parent / "tools"
        self.default_tools = []
        self.logger = logger
        # Ideally the data retrieved after executing tool should be send online to our database (after filtering), for future fine-tuning, so we can improve the models and provide them back to the community.

    def clean_tool_calls(self, tool_calls: List[ChatCompletionMessageToolCall]):
        """Clean the tool calls to replace any '.' in the name with ' _'."""
        for tool_call in tool_calls:
            tool_call.function.name = tool_call.function.name.replace(".", "_")
        return tool_calls

    def save_tool(self, function, name):
        path = os.path.join(self.tools_folder / f"{name}.py")
        with open(path, "w") as f:
            f.write(function)

    def get_tool(self, name: str) -> Callable:
        with warnings.catch_warnings():
            # Filter ResourceWarnings to ignore unclosed file objects
            warnings.filterwarnings("ignore", category=ResourceWarning)

            # Dynamically import the module
            module = importlib.import_module(f"{self.module_path}.{name}")

        # Retrieve the function with the same name as the module
        tool_function = getattr(module, name, None)

        if tool_function is None:
            raise AttributeError(f"No function named '{name}' found in module '{name}'")

        return tool_function

    def get_all_tools(self) -> List[str]:
        module_names = []

        # Use glob to find all Python files in the specified folder
        python_files = glob.glob(os.path.join(self.tools_folder, "*.py"))
        python_files = [file for file in python_files if "__init__" not in file]

        for file_path in python_files:
            # Remove the file extension and path to get the module name
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            module_names.append(module_name)

        return module_names

    # TODO: refactor to remove the call here, we should just save the signature and send it to supabase.
    def get_function_signatures(
        self,
        tool_calls: List[ChatCompletionMessageToolCall],
        functions: List[Callable],
        chat: Optional[Chat] = None,
    ) -> List[Tool]:
        tool_calls = self.clean_tool_calls(tool_calls)

        functions_dict = {}
        for function in functions:
            functions_dict[function.__name__] = function

        tools_result: List[Tool] = []
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
                # TODO: DON'T EXECUTE!! SEND THE ARGS!
                response = function(**call_arguments_dict)
                args_string = "\n".join(
                    [f"{key}={value!r}" for key, value in call_arguments_dict.items()]
                )
                self.logger.info(
                    f"Function: {function.__name__}\n{args_string}\nResponse: {response}"
                )
            except Exception as e:
                response = f"Error while executing function {function_name} with arguments {call_arguments_dict}. Error: {e}"
                self.logger.error(response)
            if chat:
                chat.add_tool_feedback(id=tool_call.id, message=response)
            tools_result.append(Tool(name=function_name, feedback=response))
        return tools_result
