from abc import ABC, abstractmethod
import json
from typing import Any, Callable, Dict, List, Optional
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
import re
import uuid
import inspect

from aware.agent.database.agent_database_handler import AgentDatabaseHandler
from aware.chat.conversation_schemas import ToolResponseMessage
from aware.chat.parser.pydantic_parser import PydanticParser
from aware.config.config import Config
from aware.database.weaviate.memory_manager import MemoryManager
from aware.process.process_info import ProcessInfo
from aware.utils.logger.process_loger import ProcessLogger
from aware.tools.capability.capability_registry import CapabilityRegistry
from aware.tools.helpers.function_call import FunctionCall
from aware.tools.decorators import IS_DEFAULT_FUNCTION, IS_TOOL, RUN_REMOTE
from aware.tools.tool_new import Tool
from aware.tools.database.tool_database_handler import ToolDatabaseHandler


class Capability(ABC):
    def __init__(
        self,
        process_info: ProcessInfo,
    ):
        self.process_info = process_info
        self.agent_data = process_info.agent_data
        self.process_ids = process_info.process_ids
        self.process_data = process_info.process_data
        self.process_logger = ProcessLogger(
            user_id=self.process_ids.user_id,
            agent_name=self.agent_data.name,
            process_name=self.process_data.name,
        )
        self.logger = self.process_logger.get_logger(self.get_name())

        self.memory_manager = MemoryManager(
            user_id=self.process_ids.user_id, logger=self.logger
        )

        # TODO: Implement also CapabilityDatabaseHandler
        self.tool_database_handler = ToolDatabaseHandler()
        self.tools = self.get_tools()

        self._tools_dict: Dict[str, Tool] = {}
        for tool in self.tools:
            self._tools_dict[tool.name] = tool

        # TODO: we need a way to update the variable when using a tool. Maybe a wrapper that initializes tool then calls the function and then updates the variable.
        # TODO: vars = self.get_capability_vars() # Use it to hold internal state of each capability.
        # TODO: selt.iterations = vars[iterations]
        self.iterations = 0

    def clean_tool_call(
        self, tool_call: ChatCompletionMessageToolCall
    ) -> ChatCompletionMessageToolCall:
        """Clean the tool call to replace any '.' in the name with ' _'."""
        tool_call.function.name = tool_call.function.name.replace(".", "_")
        return tool_call

    def _construct_arguments_dict(self, func: Callable, content: str):
        signature = inspect.signature(func)
        args = list(signature.parameters.keys())
        if not args:
            raise ValueError("Default function must have one argument.")
        if len(args) > 1:
            raise ValueError(
                f"Default function must have only one argument, {len(args)} wer1e given."
            )
        return {args[0]: content}

    def get_process_name(self) -> str:
        return self.process_data.name

    @classmethod
    def get_description(cls):
        return cls.__doc__

    @classmethod
    def get_name(cls):
        # Convert class name to snake_case
        return cls.get_snake_case_name(__class__.__name__)

    @classmethod
    def get_snake_case_name(cls, name: str):
        # Convert from CamelCase to snake_case
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        return name

    def _get_callables(self, attribute_name: str) -> List[Callable]:
        callables: List[Callable] = []
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if (
                callable(attr)
                and hasattr(attr, attribute_name)
                and getattr(attr, attribute_name)
            ):
                callables.append(attr)
        return callables

    def _get_all_callables(self) -> List[Callable]:
        callables: List[Callable] = []
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr):
                callables.append(attr)
        return callables

    def get_openai_tools(self) -> List[ChatCompletionMessageToolCall]:
        callables = self._get_callables(attribute_name=IS_TOOL)
        return [PydanticParser.get_openai_tool(callable) for callable in callables]

    def get_filtered_openai_tools(
        self, tool_names
    ) -> List[ChatCompletionMessageToolCall]:
        openai_tools = self.get_openai_tools()
        return [tool for tool in openai_tools if tool["function"]["name"] in tool_names]

    def get_tools(self) -> List[Tool]:
        tools: List[Tool] = []
        callables = self._get_callables(attribute_name=IS_TOOL)

        for callable in callables:
            params = {
                name: (param.annotation, param.default is not inspect.Parameter.empty)
                for name, param in inspect.signature(callable).parameters.items()
                if name != "self"  # Skip the 'self' parameter
            }
            docstring = inspect.getdoc(callable) or "No docstring provided"

            # Create and add the Tool object to the tools list
            tools.append(
                Tool(
                    name=callable.__name__,
                    parameters=params,
                    description=docstring,
                    callback=callable,
                    should_continue=self.iterations < Config().max_iterations,
                    run_remote=getattr(callable, RUN_REMOTE, False),
                )
            )
        return tools

    # This function helps us to select the tool and use it with call_arguments_dict, TODO: Rethink name and logic with execute_tool at ProcessInterface, maybe we can remove FunctionCall.
    def get_function_call(
        self, tool_call: ChatCompletionMessageToolCall
    ) -> Optional[FunctionCall]:
        tool_call = self.clean_tool_call(tool_call)
        try:
            function_name = tool_call.function.name
            tool = self._tools_dict[function_name]

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
                should_continue=tool.should_continue,
            )
            return function_call
        except Exception as e:
            self.logger.error(
                f"Error while retrieving signature for function {function_name} with arguments {call_arguments_dict}. Error: {e}"
            )
            return None

    def execute_tool(self, function_call: FunctionCall) -> ToolResponseMessage:
        try:
            tool = self._tools_dict[function_call.name]
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

    def get_default_tool_call(
        self, content: str
    ) -> Optional[ChatCompletionMessageToolCall]:
        callables = self._get_callables(IS_DEFAULT_FUNCTION)
        if len(callables) > 0:
            attr = callables[0]  # This assumes only one default function.
            arguments_dict = self._construct_arguments_dict(attr, content)
            arguments_json = json.dumps(arguments_dict)
            function_call = ChatCompletionMessageToolCall(
                id=str(uuid.uuid4()),
                function=Function(arguments=arguments_json, name=attr.__name__),
                type="function",
            )
            return function_call
        return None

    def is_process_finished(self) -> bool:
        return self.finished

    def update_agent_data(self):
        return AgentDatabaseHandler().update_agent_data(
            agent_data=self.agent_data,
        )

    def finish_process(self):
        self.finished = True


class FunctionDetail:
    def __init__(
        self,
        name: str,
        args: Dict[str, Any],
        description: str,
        callback: Callable,
        should_continue: bool,
    ):
        self.name = name
        self.args = args
        self.description = description
        self.callback = callback
        self.should_continue = should_continue
