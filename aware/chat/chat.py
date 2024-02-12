from typing import Callable, Dict, List, Tuple, TYPE_CHECKING
import uuid

from aware.chat.call_info import CallInfo
from aware.chat.conversation import Conversation
from aware.chat.conversation_schemas import SystemMessage
from aware.chat.parser.pydantic_parser import PydanticParser
from aware.prompts.load import load_prompt_from_args
from aware.process.process_ids import ProcessIds
from aware.utils.helpers import get_current_date
from aware.utils.logger.file_logger import FileLogger

if TYPE_CHECKING:
    from aware.data.database.client_handlers import ClientHandlers


class Chat:
    """Main class to communicate with the models and update the conversation."""

    def __init__(
        self,
        process_ids: ProcessIds,
        process_name: str,
        prompt_kwargs: Dict[str, str],
        logger: FileLogger,
    ):
        self.process_ids = process_ids
        self.process_name = process_name

        self.system_message = self.get_system(
            prompt_kwargs=prompt_kwargs,
        )
        self.conversation = Conversation(process_id=self.process_ids.process_id)
        self.redis_handler = ClientHandlers().get_redis_handler()

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

    def request_response(self, functions: List[Callable]):
        self.conversation.trim_conversation()

        function_schemas = []
        for function in functions:
            # TODO: Can we save this already on Supabase so we don't need to convert it again?
            function_schemas.append(PydanticParser.get_function_schema(function))

        call_info = CallInfo(
            call_id=str(uuid.uuid4()),
            process_ids=self.process_ids,
            process_name=self.process_name,
            system_message=self.system_message,
            functions=function_schemas,
        )
        self.redis_handler.add_call_info(call_info)
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
