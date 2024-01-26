from typing import Any, Dict


from aware.agent.agent import Agent
from aware.chat.conversation_schemas import AssistantMessage, UserMessage
from aware.chat.conversation_buffer import ConversationBuffer
from aware.config.config import Config
from aware.data.database.client_handlers import ClientHandlers
from aware.events.assistant_message import AssistantMessageEvent
from aware.memory.user.user_data import UserData
from aware.process.process import Process
from aware.server.celery_app import app as celery_app
from aware.utils.logger.file_logger import FileLogger


@celery_app.task(name="assistant.handle_user_message")
def handle_user_message(data: Dict[str, Any]):
    try:
        log = FileLogger("migration_tests", should_print=True)
        user_id = data["user_id"]
        content = data["content"]
        log.info(f"Processing new user message: {content}")

        user_data = ClientHandlers().get_user_data(user_id)
        user_message = UserMessage(name=user_data.user_name, content=content)

        assistant_agent_data = ClientHandlers().get_agent_data(
            agent_id=user_data.assistant_agent_id
        )

        # Add message to assistant conversation. (Also with buffer is true.)
        ClientHandlers().add_message(
            user_id=user_data.user_id,
            process_id=assistant_agent_data.main_process_id,
            json_message=user_message.to_json(),
        )

        # TODO: Get assistant name from database, on profile!
        Process(
            user_id=user_data.user_id, process_id=assistant_agent_data.main_process_id
        ).preprocess(
            module_name="assistant",
            prompt_name="assistant",
            agent_name="Aware",
            extra_kwargs={
                "assistant_name": Config().assistant_name,
                "context": assistant_agent_data.context,
                "thought": assistant_agent_data.thought,
                "requests": "",  # TODO: Fill this properly.
            },
        )

        # Add thought generator message.
        ClientHandlers().add_message(
            user_id=user_data.user_id,
            process_id=assistant_agent_data.thought_generator_process_id,
            json_message=user_message.to_json(),
        )
        # Trigger thought generator.
        Process(
            user_id=user_data.user_id,
            process_id=assistant_agent_data.thought_generator_process_id,
        ).preprocess(
            module_name="assistant",
            prompt_name="thought_generator",
            extra_kwargs={
                "assistant_name": Config().assistant_name,
                "user_name": user_data.user_name,
                "profile": assistant_agent_data.profile.to_string(),
                "context": assistant_agent_data.context,
            },
        )

        manage_conversation_buffer(user_data.to_json(), assistant_agent_data.to_json())
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
            json_message=assistant_message.to_json(),
        )

        manage_conversation_buffer(user_data.to_json(), assistant_agent_data.to_json())
    except Exception as e:
        log.error(f"Error: {e}")


# TODO: We can merge both into a single process - Data Storage Manager, removing Context Manager and asking for that info on Stop!!
def manage_conversation_buffer(user_data_json: str, agent_data_json: str):
    user_data = UserData.from_json(user_data_json)
    agent_data = Agent.from_json(agent_data_json)

    assistant_conversation_buffer = ConversationBuffer(
        process_id=agent_data.main_process_id
    )

    if assistant_conversation_buffer.should_trigger_warning():
        Process(
            user_id=user_data.user_id,
            process_id=agent_data.data_storage_manager_process_id,
        ).preprocess(
            module_name="assistant",
            prompt_name="data_storage_manager",
            extra_kwargs={
                "assistant_name": Config().assistant_name,
                "assistant_conversation": assistant_conversation_buffer.to_string(),
                "user_name": user_data.user_name,
                "profile": agent_data.profile.to_string(),
                "context": agent_data.context,
            },
        )

        Process(
            user_id=user_data.user_id,
            process_id=agent_data.context_manager_process_id,
        ).preprocess(
            module_name="assistant",
            prompt_name="context_manager",
            extra_kwargs={
                "assistant_name": Config().assistant_name,
                "assistant_conversation": assistant_conversation_buffer.to_string(),
                "user_name": user_data.user_name,
                "profile": agent_data.profile.to_string(),
                "context": agent_data.context,
            },
        )

        # Reset conversation buffer.
        assistant_conversation_buffer.reset()
