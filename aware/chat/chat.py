from typing import Any, Callable, Dict, List, Optional, Tuple
from logging import getLogger
from openai.types.chat import (
    ChatCompletionMessageToolCall,
)

from aware.chat.conversation import Conversation
from aware.chat.parser.pydantic_parser import PydanticParser
from aware.models.models_manager import ModelsManager
from aware.prompts.load import load_prompt_from_args
from aware.utils.helpers import get_current_date
from aware.utils.logger.file_logger import FileLogger

# TODO: Create our own logger.
LOG = getLogger(__name__)


class Chat:
    """Main class to communicate with the models and update the conversation."""

    def __init__(
        self,
        module_name: str,
        logger: FileLogger,
        system_prompt_kwargs: Dict[str, Any] = {},
        user_name: Optional[str] = None,
        assistant_name: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.module_name = module_name
        self.model = ModelsManager().create_model(self.module_name, logger, api_key)
        self.user_name = user_name
        self.assistant_name = assistant_name

        # Init conversation
        self.conversation = Conversation(module_name, self.model.get_name())
        self.system_instruction_message = self.load_prompt(
            "system", self.module_name, system_prompt_kwargs
        )
        system_message = self.update_system()
        self.conversation.add_system_message(system_message)
        self.logger = logger

    def add_tool_feedback(self, id: str, message: str):
        self.conversation.add_tool_message(id=id, message=message)

    def call(
        self,
        functions: List[Callable] = [],
    ):
        """Call the model to get a response."""
        self.update_system()

        function_schemas = []
        for function in functions:
            function_schemas.append(PydanticParser.get_function_schema(function))
        response = self.model.get_response(
            conversation=self.conversation,
            functions=function_schemas,
        )
        if function_schemas:
            tool_calls = response.tool_calls
            if tool_calls is not None:
                tool_calls = self.clean_tool_calls(response.tool_calls)
                # In case we are sending tools we should save them in the traces as OpenAI doesn't include them on prompt.
                self.conversation.add_assistant_tool_message(
                    tool_calls, assistant_name=self.assistant_name
                )
                self.log_conversation()
                return tool_calls

        return response.content

    def clean_tool_calls(self, tool_calls: List[ChatCompletionMessageToolCall]):
        """Clean the tool calls to replace any '.' in the name with ' _'."""
        for tool_call in tool_calls:
            tool_call.function.name = tool_call.function.name.replace(".", "_")
        return tool_calls

    def edit_system_message(self, system_prompt_kwargs: Dict[str, Any]):
        """Edit the system message."""
        self.system_instruction_message = self.load_prompt(
            "system", self.module_name, system_prompt_kwargs
        )
        system = self.update_system()
        self.conversation.edit_system_message(system)

    def get_response(
        self,
        prompt_kwargs: Dict[str, Any],
        functions: List[Callable] = [],
        user_name: Optional[str] = None,
        assistant_name: Optional[str] = None,
    ) -> str | List[ChatCompletionMessageToolCall]:
        """Get a reponse from the model, can be a single string or a list of tool call."""
        # Add user message
        prompt = self.load_prompt("user", self.module_name, prompt_kwargs)
        self.conversation.add_user_message(prompt, user_name)

        return self.call(functions, assistant_name=assistant_name)

    def get_conversation(self):
        return self.conversation

    def get_remaining_tokens(self) -> Tuple[int, bool]:
        """Returns the remaining tokens of the conversation and if it should trigger a warning."""
        return (
            self.conversation.get_remaining_tokens(),
            self.conversation.should_trigger_warning(),
        )

    def load_prompt(
        self, prompt_name: str, path: Optional[str] = None, args: Dict[str, Any] = {}
    ):
        return load_prompt_from_args(prompt_name, **args)

    def update_system(self):
        self.system = self.load_prompt(
            "system_meta",
            args={
                "date": get_current_date(),
                "instruction": self.system_instruction_message,
            },
        )
        return self.system

    def log_conversation(self):
        """Log the conversation."""
        self.logger.info(
            f"--- CONVERSATION ---\n{self.conversation.to_string()}",
            should_print_local=False,
        )
