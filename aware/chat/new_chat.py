from typing import Any, Callable, Dict, List, Optional, Tuple
from openai.types.chat import (
    ChatCompletionMessageToolCall,
)
import uuid

from aware.chat.parser.pydantic_parser import PydanticParser
from aware.prompts.load import load_prompt_from_args, load_prompt_from_database
from aware.utils.helpers import get_current_date
from aware.utils.logger.file_logger import FileLogger

from aware.chat.new_conversation_schemas import (
    ToolResponseMessage,
    UserMessage,
)
from aware.chat.call_info import CallInfo
from aware.data.database.client_handlers import ClientHandlers
from aware.chat.new_conversation import Conversation


class Chat:
    """Main class to communicate with the models and update the conversation."""

    def __init__(
        self,
        process_name: str,
        user_id: str,
        chat_id: str,
        logger: FileLogger,
    ):
        self.process_name = process_name
        self.user_id = user_id
        self.chat_id = chat_id

        # Init conversation
        system_instruction_message = load_prompt_from_database(
            self.process_name,
            user_id,
        )
        self.system_message = self.get_system(
            system_instruction_message=system_instruction_message
        )
        self.conversation = Conversation(
            chat_id=chat_id, user_id=user_id, process_name=process_name
        )

        # Redis handler
        self.redis_handler = ClientHandlers().get_redis_handler()

        # Logger
        self.logger = logger

    # TODO: REMOVE! Should not be on conversation
    # def add_existing_message(self, chat_message: ChatMessage):
    #     self.conversation.add_existing_message(chat_message)

    # def add_new_message(self, message: JSONMessage):
    #     self.conversation.add_new_message(message)

    # TODO: Interact with REDIS - SUPABASE to save tool feedback
    # TODO: MOVE TO CONVERSATION. THIS SHOULD NOT BE ON CHAT AS CHAT WILL NOT WAIT.
    def add_tool_feedback(self, id: str, message: str):
        tool_response_message = ToolResponseMessage(content=message, tool_call_id=id)
        self.conversation.on_new_message(tool_response_message)

    # TODO: Remove - Each process should add this manually.
    def get_response(
        self,
        prompt_kwargs: Dict[str, Any],
        functions: List[Callable] = [],
        user_name: Optional[str] = None,
    ) -> str | List[ChatCompletionMessageToolCall]:
        """Get a reponse from the model, can be a single string or a list of tool call."""
        # Add user message
        prompt = self.load_prompt("user", self.process_name, prompt_kwargs)
        self.conversation.on_new_message(UserMessage(name=user_name, content=prompt))

        return self.call(functions)

    def get_conversation(self):
        return self.conversation

    # TODO: Check how to this efficiently.
    def get_remaining_tokens(self) -> Tuple[int, bool]:
        """Returns the remaining tokens of the conversation and if it should trigger a warning."""
        return (
            self.conversation.get_remaining_tokens(),
            self.conversation.should_trigger_warning(),
        )

    def get_system(self, system_instruction_message: str):
        self.system = load_prompt_from_args(
            "system_meta",
            args={
                "date": get_current_date(),
                "instruction": system_instruction_message,
            },
        )
        return self.system

    def request_response(self, functions: List[Callable]):
        self.conversation.trim_conversation()

        function_schemas = []
        for function in functions:
            # TODO: Can we save this already on Supabase so we don't need to convert it again?
            function_schemas.append(PydanticParser.get_function_schema(function))

        call_info = CallInfo(
            user_id=self.user_id,
            call_id=str(uuid.uuid4()),
            process_name=self.process_name,
            chat_id=self.chat_id,
            system_message=self.system_message,
            functions=function_schemas,
        )
        self.redis_handler.add_call_info(call_info)

    # Not used, should be moved to server when we process requests to log them all.
    def log_conversation(self):
        """Log the conversation."""
        self.logger.info(
            f"--- CONVERSATION ---\n{self.conversation.to_string()}",
            should_print_local=False,
        )
