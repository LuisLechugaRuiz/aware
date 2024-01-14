from typing import Any, Dict

from aware.agent.memory.new_working_memory import WorkingMemory
from aware.assistant.assistant import Assistant
from aware.data.database.client_handlers import ClientHandlers
from aware.server.celery_app import app as celery_app
from aware.utils.logger.file_logger import FileLogger
from aware.utils.helpers import get_current_date_iso8601


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
            supabase_handler = ClientHandlers().get_supabase_handler()
            redis_handler = ClientHandlers().get_redis_handler()
            working_memory = redis_handler.get_working_memory(user_id)

            if working_memory is None:
                log.info("Working memory not found in Redis")
                # Fetch user data from Supabase
                working_memory = supabase_handler.get_working_memory(user_id)
                user_profile = supabase_handler.get_user_profile(user_id)
                if user_profile is None:
                    raise Exception("User profile not found")
                if working_memory is None:
                    # Create empty working memory
                    working_memory = WorkingMemory(
                        user_id=user_id,
                        chat_id=chat_id,
                        user_name=user_profile["display_name"],
                        thought="",
                        context="",
                        updated_at=get_current_date_iso8601(),
                    )
                    supabase_handler.set_working_memory(working_memory)
                # Store in Redis
                redis_handler.set_working_memory(working_memory)
            else:
                log.info("Working memory found in Redis")
            assistant_response.delay(working_memory.to_json(), content)
            # thought_generator.delay(working_memory, content)  # TODO :IMPLEMENT ME
        elif role == "assistant":
            log = FileLogger("migration_tests_assistant", should_print=True)
            log.info(f"PROCESSING NEW ASSISTANT MESSAGE: {content}")
            # TODO: Trigger Context Manager.
    except Exception as e:
        log.error(f"Error: {e}")


@celery_app.task(name="assistant.get_response")
def assistant_response(working_memory_json: str, user_message: str):
    working_memory = WorkingMemory.from_json(working_memory_json)
    Assistant(working_memory).on_user_message(
        user_name=working_memory.user_name, message=user_message
    )
