from openai.types.chat import ChatCompletionMessage

from aware.assistant.assistant import Assistant
from aware.chat.call_info import CallInfo
from aware.server.celery_app import app as celery_app
from aware.utils.logger.file_logger import FileLogger


# TODO: Create a simple factory that returns the Process name, invert the logic of get_process_name.
@celery_app.task(name="system.process_model_response")
def process_model_response(response: str, call_info: CallInfo):
    # we need to check if have tool_calls at the processes
    logger = FileLogger("migration_tests")
    logger.info(f"Task process_response started with message: {response}")
    # 1. Reconstruct response.
    openai_response = ChatCompletionMessage.model_validate_json(response)
    # 2. Upload message to Supabase and Redis.

    # 3. If is a string then try to call default_tool_calls and get signature or stop.
    # 4. If tools calls then route message to correct process.
    if (
        call_info.process_name == Assistant.get_process_name()
    ):  # Then add to Supabase and send to user:
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


# TODO: Can have multiple tools.
@celery_app.task(name="system.process_tool_feedback")
def process_tool_feedback(tool_name: str, feedback: str, call_info: CallInfo):
    pass
