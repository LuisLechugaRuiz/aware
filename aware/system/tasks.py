from openai.types.chat import ChatCompletionMessage

from aware.agent.process import Process
from aware.assistant.assistant import Assistant
from aware.data.database.client_handlers import ClientHandlers
from aware.chat.call_info import CallInfo
from aware.chat.new_conversation_schemas import AssistantMessage, ToolCalls
from aware.config.config import Config
from aware.server.celery_app import app as celery_app
from aware.utils.logger.file_logger import FileLogger


# TODO: THIS IS NOT SYSTEM TASK, THIS IS SERVER TASK!!!


@celery_app.task(name="system.process_model_response")
def process_model_response(response_str: str, call_info_str: str):
    # we need to check if have tool_calls at the processes
    logger = FileLogger("migration_tests")
    logger.info(f"Task process_response started with message: {response_str}")

    # TODO: Get assistant name from specific user.
    assistant_name = Config().assistant_name

    try:
        # 1. Get process.
        call_info = CallInfo.from_json(call_info_str)

        process = get_process(
            process_name=call_info.process_name,
            user_id=call_info.user_id,
            chat_id=call_info.chat_id,
        )
        process.postprocess()

        # 2. Reconstruct response.
        openai_response = ChatCompletionMessage.model_validate_json(response_str)
        tool_calls = openai_response.tool_calls
        if tool_calls is not None:
            new_message = ToolCalls.from_openai(
                assistant_name=Config().assistant_name,
                tool_calls=openai_response.tool_calls,
            )
        else:
            tool_calls = [process.get_default_tool_call(openai_response.content)]
            if tool_calls is not None:
                new_message = ToolCalls.from_openai(
                    assistant_name=assistant_name,
                    tool_calls=tool_calls,
                )
            else:
                new_message = AssistantMessage(
                    name=assistant_name, content=openai_response.content
                )
                process.stop_agent()

        logger.info("Adding message to redis and supabase")
        # 3. Upload message to Supabase and Redis.
        ClientHandlers().add_message(
            chat_id=call_info.chat_id,
            user_id=call_info.user_id,
            process_name=call_info.process_name,
            json_message=new_message,
        )

        logger.info("Getting function calls")
        # 4. Get function calls
        if tool_calls:
            function_calls = process.get_function_calls(tool_calls)
            if process.run_remote:
                # TODO: Call supabase real-time client.
                pass
            else:
                logger.info("Executing function calls")
                process.execute_tools(function_calls)
    except Exception as e:
        logger.error(f"Error in process_response: {e}")


def get_process(process_name: str, user_id: str, chat_id: str) -> Process:
    if (
        process_name == Assistant.get_process_name()
    ):  # Then add to Supabase and send to user:
        return Assistant(user_id=user_id, chat_id=chat_id)
    elif process_name == "thought_generator":
        # Then run thought generator processing.
        pass
    elif "context_manager":
        # Then run context manager processing.
        pass
    elif "data_storage_manager":  # Then add to Supabase and
        pass
    elif "system":
        pass
    else:
        raise Exception("Unknown process name.")


# TODO: Can have multiple tools.
@celery_app.task(name="system.process_tool_feedback")
def process_tool_feedback(tool_name: str, feedback: str, call_info: CallInfo):
    pass