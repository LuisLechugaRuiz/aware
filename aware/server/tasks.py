from aware.chat.call_info import CallInfo
from aware.server.celery_app import app as celery_app
from aware.utils.logger.file_logger import FileLogger


# TODO: MOVE TO SERVER AND CREATE NEW WORKERS!
@celery_app.task(name="server.process_response")
def process_response(response: str, call_info: CallInfo):
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
