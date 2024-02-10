from typing import Any, Dict

from aware.chat.conversation_schemas import UserMessage
from aware.data.database.client_handlers import ClientHandlers
from aware.process.process_handler import ProcessHandler
from aware.server.celery_app import app as celery_app
from aware.utils.logger.file_logger import FileLogger


@celery_app.task(name="assistant.handle_user_message")
def handle_user_message(data: Dict[str, Any]):
    try:
        logger = FileLogger("migration_tests", should_print=True)
        user_id = data["user_id"]
        content = data["content"]
        logger.info(f"Processing new user message: {content}")

        user_data = ClientHandlers().get_user_data(user_id)
        agent_id = ClientHandlers().get_agent_data

        user_message = UserMessage(name=user_data.user_name, content=content)
        process_ids = ProcessHandler().get_process_ids(user_id, agent_id, "main")

        process_handler = ProcessHandler(process_ids=process_ids)
        process_handler.add_message(message=user_message)
        process_handler.on_transition()
    except Exception as e:
        logger.error(f"Error: {e}")
