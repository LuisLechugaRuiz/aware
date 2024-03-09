from typing import Any, Dict, List, Tuple
import uuid
from openai.types.chat import ChatCompletionMessageToolCall

from aware.chat.call_info import CallInfo
from aware.chat.conversation import Conversation
from aware.chat.conversation_schemas import SystemMessage
from aware.chat.database.chat_database_handler import ChatDatabaseHandler
from aware.prompts.load import load_prompt_from_args
from aware.process.process_ids import ProcessIds
from aware.utils.helpers import get_current_date
from aware.utils.logger.file_logger import FileLogger


class Chat:
    """Main class to communicate with the models and update the conversation."""

    def __init__(
        self,
        name: str,
        process_ids: ProcessIds,
        prompt_kwargs: Dict[str, str],
        logger: FileLogger,
    ):
        self.process_ids = process_ids
        self.name = name

        self.system_message = self.get_system(
            prompt_kwargs=prompt_kwargs,
        )
        self.conversation = Conversation(process_id=self.process_ids.process_id)
        self.chat_database_handler = ChatDatabaseHandler()

        self.logger = logger

    def get_conversation(self):
        return self.conversation

    # TODO: Check how to this efficiently.
    def get_remaining_tokens(self) -> Tuple[int, bool]:
        """Returns the remaining tokens of the conversation and if it should trigger a warning."""
        return (
            self.conversation.get_remaining_tokens(),
            self.conversation.should_trigger_warning(),
        )

    def get_system(
        self,
        prompt_kwargs: Dict[str, str],
    ):
        args = {
            "date": get_current_date(),
        }
        args.update(prompt_kwargs)
        return load_prompt_from_args("meta", args=args)

    def request_response(self, tools_openai: List[ChatCompletionMessageToolCall]):
        self.conversation.trim_conversation()

        call_info = CallInfo(
            call_id=str(uuid.uuid4()),
            name=self.name,
            process_ids=self.process_ids,
            system_message=self.system_message,
            tools_openai=tools_openai,
        )
        self.chat_database_handler.add_call_info(call_info)
        self.log_conversation()

    # TODO: SHOULD BE USED TO STORE ALL TRACES!!
    def log_conversation(self):
        """Log the conversation."""
        system_message_str = SystemMessage(self.system_message).to_string()
        conversation = f"{system_message_str}\n{self.conversation.to_string()}"
        self.logger.info(
            f"--- CONVERSATION ---\n{conversation}",
            should_print_local=False,
        )
