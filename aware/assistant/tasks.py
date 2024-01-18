import json
from typing import Any, Dict

from aware.agent.memory.new_working_memory import WorkingMemory
from aware.assistant.assistant import Assistant
from aware.chat.new_conversation_schemas import ChatMessage, UserMessage
from aware.data.database.client_handlers import ClientHandlers
from aware.server.celery_app import app as celery_app
from aware.utils.logger.file_logger import FileLogger


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

        # 1. Add to redis.
        chat_message = ChatMessage.from_json(chat_message_json, UserMessage)
        redis_handler = ClientHandlers().redis_handler
        redis_handler.add_message(working_memory.chat_id, chat_message)

        # 2. Request assistant response.
        log.info("New user message")
        prompt_kwargs = Assistant.get_system_prompt_kwargs(
            working_memory=working_memory
        )
        assistant = Assistant(
            user_id=working_memory.user_id, chat_id=working_memory.chat_id
        ).preprocess(prompt_kwargs)
        assistant.on_user_message()
    except Exception as e:
        log.error(f"Error in assistant_response: {e}")
