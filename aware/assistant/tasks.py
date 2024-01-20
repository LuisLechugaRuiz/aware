import json
from typing import Any, Dict

from aware.agent.memory.user_data import UserData
from aware.assistant.assistant import Assistant
from aware.chat.new_conversation_schemas import ChatMessage, UserMessage
from aware.data.database.client_handlers import ClientHandlers
from aware.server.celery_app import app as celery_app
from aware.utils.logger.file_logger import FileLogger


@celery_app.task(name="assistant.handle_new_message")
def handle_new_message(data: Dict[str, Any]):
    try:
        log = FileLogger("migration_tests", should_print=True)
        user_id = data["user_id"]
        chat_id = data["chat_id"]
        role = data["role"]
        content = data["content"]
        if role == "user":
            log.info(f"PROCESSING NEW USER MESSAGE: {content}")

            user_data = ClientHandlers().get_user_data(user_id, chat_id)

            # TODO: Should we group these tasks?
            log.info("DEBUG PRE")
            user_message = UserMessage(name=user_data.user_name, content=content)
            chat_message = ChatMessage(
                message_id=data["id"],
                timestamp=data["created_at"],
                message=user_message,
            )
            redis_handler = ClientHandlers().redis_handler
            redis_handler.add_message(user_data.chat_id, chat_message)
            log.info(
                f"Task assistant_response started with message: {chat_message.to_string()}"
            )
            assistant_response.delay(user_data.to_json())
            log.info("DEBUG POST")

            # thought_generator.delay(user_data.to_json())  # TODO :IMPLEMENT ME
        elif role == "assistant":
            log = FileLogger("migration_tests_assistant", should_print=True)
            log.info(f"PROCESSING NEW ASSISTANT MESSAGE: {content}")
            # TODO: Trigger Context Manager.
    except Exception as e:
        log.error(f"Error: {e}")


@celery_app.task(name="assistant.get_response")
def assistant_response(user_data_json: str):
    log = FileLogger("migration_tests", should_print=True)

    try:
        log.info("New user message")
        user_data = UserData.from_json(user_data_json)
        assistant = Assistant(
            user_id=user_data.user_id, chat_id=user_data.chat_id
        ).preprocess()
        assistant.on_user_message()
    except Exception as e:
        log.error(f"Error in assistant_response: {e}")
