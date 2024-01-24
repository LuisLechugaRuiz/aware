from typing import Any, Dict

from aware.assistant.assistant import Assistant
from aware.assistant.user.context_manager.user_context_manager import (
    UserContextManager,
)
from aware.assistant.user.data_storage.user_data_storage_manager import (
    UserDataStorageManager,
)
from aware.assistant.user.thought_generator.user_thought_generator import (
    UserThoughtGenerator,
)
from aware.chat.conversation_schemas import AssistantMessage, UserMessage
from aware.chat.conversation import Conversation
from aware.config.config import Config
from aware.data.database.client_handlers import ClientHandlers
from aware.events.assistant_message import AssistantMessageEvent
from aware.memory.user.user_data import UserData
from aware.memory.user.user_profile import UserProfile
from aware.server.celery_app import app as celery_app
from aware.utils.logger.file_logger import FileLogger


def add_conversation_buffer_message(user_data_json: str, json_message: str):
    user_data = UserData.from_json(user_data_json)

    # Add message to assistant conversation buffer (for future storage).
    conversation_buffer = f"{Assistant.get_process_name()}_conversation_buffer"
    ClientHandlers().add_message(
        chat_id=user_data.chat_id,
        user_id=user_data.user_id,
        process_name=conversation_buffer,
        json_message=json_message,
    )
    assistant_conversation_buffer = Conversation(
        chat_id=user_data.chat_id,
        user_id=user_data.user_id,
        process_name=conversation_buffer,
    )

    if assistant_conversation_buffer.should_trigger_warning():
        user_profile = UserProfile(user_data.user_id)

        user_data_storage_manager = UserDataStorageManager(
            user_id=user_data.user_id,
            chat_id=user_data.chat_id,
        ).preprocess(
            extra_kwargs={
                "assistant_name": Config().assistant_name,
                "assistant_conversation": assistant_conversation_buffer.to_string(),
                "user_name": user_data.user_name,
                "user_profile": user_profile.to_string(),
            }
        )
        user_data_storage_manager.request_response()

        user_context_manager = UserContextManager(
            user_id=user_data.user_id,
            chat_id=user_data.chat_id,
        ).preprocess(
            extra_kwargs={
                "assistant_name": Config().assistant_name,
                "assistant_conversation": assistant_conversation_buffer.to_string(),
                "user_name": user_data.user_name,
                "user_profile": user_profile.to_string(),
            }
        )
        user_context_manager.request_response()

        # Reset conversation buffer.
        assistant_conversation_buffer.reset()


def add_thought_generator_message(user_data_json: str, json_message: str):
    user_data = UserData.from_json(user_data_json)

    # Add message to thought generator.
    ClientHandlers().add_message(
        chat_id=user_data.chat_id,
        user_id=user_data.user_id,
        process_name=UserThoughtGenerator.get_process_name(),
        json_message=json_message,
    )


@celery_app.task(name="assistant.handle_user_message")
def handle_user_message(data: Dict[str, Any]):
    try:
        log = FileLogger("migration_tests", should_print=True)
        user_id = data["user_id"]
        chat_id = data["chat_id"]
        content = data["content"]
        log.info(f"Processing new user message: {content}")

        user_data = ClientHandlers().get_user_data(user_id, chat_id)
        user_message = UserMessage(name=user_data.user_name, content=content)

        # Add message to assistant conversation.
        ClientHandlers().add_message(
            chat_id=user_data.chat_id,
            user_id=user_data.user_id,
            process_name=Assistant.get_process_name(),
            json_message=user_message.to_json(),
        )
        assistant = Assistant(
            user_id=user_data.user_id, chat_id=user_data.chat_id
        ).preprocess()
        assistant.request_response()

        add_thought_generator_message(user_data.to_json(), user_message.to_json())
        add_conversation_buffer_message(user_data.to_json(), user_message.to_json())
    except Exception as e:
        log.error(f"Error: {e}")


@celery_app.task(name="assistant.handle_assistant_message")
def handle_assistant_message(assistant_message_event_json: str):
    try:
        log = FileLogger("migration_tests", should_print=True)

        assistant_message_event = AssistantMessageEvent.from_json(
            assistant_message_event_json
        )
        log.info(f"Processing new assistant message: {assistant_message_event.message}")
        user_data = ClientHandlers().get_user_data(
            assistant_message_event.user_id, assistant_message_event.chat_id
        )
        assistant_message = AssistantMessage(
            name=assistant_message_event.assistant_name,
            content=assistant_message_event.message,
        )
        add_thought_generator_message(user_data.to_json(), assistant_message.to_json())

        # Trigger thought generator.
        user_profile = UserProfile(user_data.user_id)
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
        user_thought_generator.request_response()

        # Add message to conversation buffer.
        add_conversation_buffer_message(
            user_data.to_json(), assistant_message.to_json()
        )
    except Exception as e:
        log.error(f"Error: {e}")
