from typing import Any, Dict

from aware.assistant.assistant import Assistant
from aware.assistant.user.user_thought_generator import UserThoughtGenerator
from aware.chat.conversation_schemas import ChatMessage, UserMessage
from aware.config.config import Config
from aware.data.database.client_handlers import ClientHandlers
from aware.memory.user.user_data import UserData
from aware.memory.user.user_profile import UserProfile
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
            log.info(
                f"Task assistant_response started with message: {chat_message.to_string()}"
            )
            assistant_response.delay(user_data.to_json(), chat_message.to_json())
            log.info("DEBUG POST")

            user_profile = UserProfile(user_data.user_id)
            thought_generator.delay(
                user_data.to_json(), chat_message.to_json(), user_profile.to_json()
            )
        elif role == "assistant":
            log = FileLogger("migration_tests_assistant", should_print=True)
            log.info(f"PROCESSING NEW ASSISTANT MESSAGE: {content}")
            # TODO: Trigger Context Manager.
    except Exception as e:
        log.error(f"Error: {e}")


@celery_app.task(name="assistant.get_response")
def assistant_response(user_data_json: str, chat_message_json: str):
    log = FileLogger("migration_tests", should_print=True)

    try:
        log.info("New user message")
        chat_message = ChatMessage.from_json(chat_message_json, UserMessage)
        user_data = UserData.from_json(user_data_json)

        redis_handler = ClientHandlers().get_redis_handler()
        redis_handler.add_message(
            chat_id=user_data.chat_id,
            process_name=Assistant.get_process_name(),
            chat_message=chat_message,
        )

        assistant = Assistant(
            user_id=user_data.user_id, chat_id=user_data.chat_id
        ).preprocess()
        assistant.on_user_message()
    except Exception as e:
        log.error(f"Error in assistant_response: {e}")


# TODO: Trigger this after assistant response, adding the response as part of the thought. This way we can easily synchronize both.
@celery_app.task(name="assistant.get_thought")
def thought_generator(
    user_data_json: str, chat_message_json: str, user_profile_json: str
):
    log = FileLogger("migration_tests", should_print=True)

    try:
        log.info("Generating thought")
        chat_message = ChatMessage.from_json(chat_message_json, UserMessage)
        user_data = UserData.from_json(user_data_json)

        redis_handler = ClientHandlers().get_redis_handler()
        redis_handler.add_message(
            chat_id=user_data.chat_id,
            process_name=UserThoughtGenerator.get_process_name(),
            chat_message=chat_message,
        )

        user_profile = UserProfile.from_json(user_data.user_id, user_profile_json)

        user_thought_generator = UserThoughtGenerator(
            user_id=user_data.user_id,
            chat_id=user_data.chat_id,
        ).preprocess(
            extra_kwargs={
                "assistant_name": Config().assistant_name,
                "user_name": user_data.user_name,
                "user_profile": user_profile.to_string(),
            }
        )
        user_thought_generator.on_user_message()
        log.info("Thought generated")
    except Exception as e:
        log.error(f"Error in generating thought: {e}")
