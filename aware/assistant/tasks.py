import json
from typing import Any, Dict

from aware.agent.memory.new_working_memory import WorkingMemory
from aware.assistant.assistant import Assistant
from aware.data.database.client_handlers import ClientHandlers
from aware.server.celery_app import app as celery_app
from aware.utils.logger.file_logger import FileLogger
from aware.chat.new_conversation_schemas import ChatMessage, UserMessage

from aware.chat.call_info import CallInfo  # TODO: REMOVE!


@celery_app.task(name="assistant.handle_new_message")
def handle_new_message(payload: Dict[str, Any]):
    try:
        log = FileLogger("migration_tests", should_print=True)
        data = payload["record"]
        user_id = data["user_id"]
        chat_id = data["chat_id"]
        role = data["role"]
        content = data["content"]
        if role == "user":
            log = FileLogger("migration_tests_user", should_print=True)
            log.info(f"PROCESSING NEW USER MESSAGE: {content}")

            working_memory = ClientHandlers().get_working_memory(user_id, chat_id)

            # TODO: Should we group these tasks?
            log.info("DEBUG PRE")
            user_message = UserMessage(name=working_memory.user_name, content=content)
            chat_message = ChatMessage(
                message_id=data["id"],
                timestamp=data["created_at"],
                message=user_message,
            )
            assistant_response.delay(working_memory.to_json(), chat_message.to_json())
            log.info("DEBUG POST")

            # thought_generator.delay(working_memory, content)  # TODO :IMPLEMENT ME
        elif role == "assistant":
            log = FileLogger("migration_tests_assistant", should_print=True)
            log.info(f"PROCESSING NEW ASSISTANT MESSAGE: {content}")
            # TODO: Trigger Context Manager.
    except Exception as e:
        log.error(f"Error: {e}")


@celery_app.task(name="assistant.get_response")
def assistant_response(working_memory_json: str, chat_message_json: str):
    log = FileLogger("migration_tests", should_print=True)
    log.info(f"Task assistant_response started with message: {chat_message_json}")

    try:
        working_memory = WorkingMemory.from_json(working_memory_json)
        chat_message = ChatMessage.from_json(chat_message_json, UserMessage)
        log.info("New user message")
        Assistant(working_memory).on_user_message(chat_message=chat_message)
    except Exception as e:
        log.error(f"Error in assistant_response: {e}")


# TODO: REMOVE BY SERVER/TASKS!
@celery_app.task(name="assistant.process_response")
def process_response(response: str, call_info: str):
    # we need to check if have tool_calls at the processes
    logger = FileLogger("migration_tests")
    logger.info(f"Task process_response started with message: {response}")
    # Route the message to the correct task and move info to databases.
    if call_info.process_name == "assistant":  # Then add to Supabase and send to user:
        pass
    elif (
        call_info.process_name == "thought_generator"
    ):  # Then run thought generator processing.
        pass
    elif (
        call_info.process_name == "context_manager"
    ):  # Then run context manager processing.
        pass
    elif call_info.process_name == "data_storage_manager":  # Then add to Supabase and
        pass
    # TODO: Add system
    else:
        raise Exception("Unknown process name.")
