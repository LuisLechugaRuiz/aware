import json
from typing import Any, Dict

from aware.chat.conversation_schemas import AssistantMessage, UserMessage
from aware.chat.conversation_buffer import ConversationBuffer
from aware.data.database.client_handlers import ClientHandlers
from aware.events.assistant_message import AssistantMessageEvent
from aware.process.process_ids import ProcessIds
from aware.server.celery_app import app as celery_app
from aware.server.tasks import preprocess
from aware.utils.logger.file_logger import FileLogger


@celery_app.task(name="assistant.handle_user_message")
def handle_user_message(data: Dict[str, Any]):
    try:
        log = FileLogger("migration_tests", should_print=True)
        user_id = data["user_id"]
        content = data["content"]
        log.info(f"Processing new user message: {content}")

        user_data = ClientHandlers().get_user_data(user_id)
        agent_id = user_data.assistant_agent_id

        user_message = UserMessage(name=user_data.user_name, content=content)

        # Add message and start main process.
        main_ids = get_process_ids(user_id, agent_id, "main")
        ClientHandlers().add_message(
            user_id=user_id,
            process_id=main_ids.process_id,
            json_message=user_message,
        )
        preprocess.delay(main_ids.to_json())

        # Add message and start thought generator.
        thought_generator_ids = get_process_ids(user_id, agent_id, "thought_generator")
        ClientHandlers().add_message(
            user_id=user_id,
            process_id=thought_generator_ids.process_id,
            json_message=user_message,
        )
        preprocess.delay(thought_generator_ids.to_json())

        manage_conversation_buffer(
            main_ids=main_ids,
        )
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
        user_data = ClientHandlers().get_user_data(assistant_message_event.user_id)
        assistant_message = AssistantMessage(
            name=assistant_message_event.assistant_name,
            content=assistant_message_event.message,
        )

        assistant_agent_data = ClientHandlers().get_agent_data(
            agent_id=user_data.assistant_agent_id
        )

        # Add thought generator message.
        ClientHandlers().add_message(
            user_id=user_data.user_id,
            process_id=assistant_agent_data.thought_generator_process_id,
            json_message=assistant_message,
        )

        manage_conversation_buffer(user_data.to_json(), assistant_agent_data.to_json())
    except Exception as e:
        log.error(f"Error: {e}")


# TODO: We can merge both into a single process - Data Storage Manager, removing Context Manager and asking for that info on Stop!!
def manage_conversation_buffer(main_ids: ProcessIds, user_name: str):
    assistant_conversation_buffer = ConversationBuffer(process_id=main_ids.process_id)

    ClientHandlers().publish(user_id=main_ids.user_id, topic_name="assistant_conversation", topic_data=assistant_conversation_buffer.to_string())

    if assistant_conversation_buffer.should_trigger_warning():
        data_storage_manager_ids = get_process_ids(
            user_id=main_ids.user_id,
            agent_id=main_ids.agent_id,
            process_name="data_storage_manager",
        )
        preprocess.delay(data_storage_manager_ids.to_json())

        context_manager_ids = get_process_ids(
            user_id=main_ids.user_id,
            agent_id=main_ids.agent_id,
            process_name="context_manager",
        )
        preprocess.delay(context_manager_ids.to_json())

        # CARE !!! Reset conversation buffer !!! - THIS CAN LEAD TO A RACE WITH THE TRIGGERS, WE NEED TO REMOVE AFTER THAT!!
        assistant_conversation_buffer.reset()


def get_process_ids(user_id: str, agent_id: str, process_name: str):
    process_id = ClientHandlers().get_agent_process_id(
        agent_id=agent_id, process_name=process_name
    )
    return ProcessIds(
        user_id=user_id,
        agent_id=agent_id,
        process_id=process_id,
    )
