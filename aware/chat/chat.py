from typing import Callable, Dict, List, Optional, Tuple
import uuid

from aware.chat.call_info import CallInfo
from aware.chat.conversation import Conversation
from aware.chat.conversation_schemas import SystemMessage
from aware.chat.parser.pydantic_parser import PydanticParser
from aware.data.database.client_handlers import ClientHandlers
from aware.prompts.load import load_prompt_from_args, load_prompt_from_database
from aware.process.process_ids import ProcessIds
from aware.utils.helpers import get_current_date
from aware.utils.logger.file_logger import FileLogger


class Chat:
    """Main class to communicate with the models and update the conversation."""

    def __init__(
        self,
        process_ids: ProcessIds,
        agent_name: str,
        module_name: str,
        prompt_name: str,
        logger: FileLogger,
        prompt_kwargs: Optional[Dict[str, str]] = {},
        meta_prompt_kwargs: Optional[Dict[str, str]] = None,
    ):
        self.process_ids = process_ids

        self.agent_name = agent_name
        self.module_name = module_name
        self.prompt_name = prompt_name

        system_instruction_message = load_prompt_from_database(
            self.prompt_name,
            self.process_ids.user_id,
            self.module_name,
            prompt_kwargs,
        )
        self.system_message = self.get_system(
            system_instruction_message=system_instruction_message,
            meta_prompt_kwargs=meta_prompt_kwargs,
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
        system_instruction_message: str,
        meta_prompt_kwargs: Optional[Dict[str, str]] = None,
    ):
        # TODO: ADJUST META PROMPT PROPERLY:
        # system_instruction_message = Task
        args = {
            "date": get_current_date(),
            "instruction": system_instruction_message,
        }
        args.update(meta_prompt_kwargs or {})
        self.system = load_prompt_from_args("meta", args=args)
        return self.system

    def request_response(self, functions: List[Callable]):
        self.conversation.trim_conversation()

        function_schemas = []
        for function in functions:
            # TODO: Can we save this already on Supabase so we don't need to convert it again?
            function_schemas.append(PydanticParser.get_function_schema(function))

        call_info = CallInfo(
            process_ids=self.process_ids,
            call_id=str(uuid.uuid4()),
            agent_name=self.agent_name,
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
