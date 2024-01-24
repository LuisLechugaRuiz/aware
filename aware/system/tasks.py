from openai.types.chat import ChatCompletionMessage

from aware.agent.process import Process
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
from aware.data.database.client_handlers import ClientHandlers
from aware.chat.call_info import CallInfo
from aware.chat.conversation_schemas import AssistantMessage, ToolCalls
from aware.server.celery_app import app as celery_app
from aware.utils.logger.file_logger import FileLogger


# TODO: THIS IS NOT SYSTEM TASK, THIS IS SERVER TASK!!!


@celery_app.task(name="system.process_model_response")
def process_model_response(response_str: str, call_info_str: str):
    # we need to check if have tool_calls at the processes
    logger = FileLogger("migration_tests")
    logger.info(f"Task process_response started with message: {response_str}")

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
                assistant_name=call_info.agent_name,
                tool_calls=openai_response.tool_calls,
            )
        else:
            tool_calls = [process.get_default_tool_call(openai_response.content)]
            if tool_calls is not None:
                new_message = ToolCalls.from_openai(
                    assistant_name=call_info.agent_name,
                    tool_calls=tool_calls,
                )
            else:
                new_message = AssistantMessage(
                    name=call_info.agent_name, content=openai_response.content
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
                tools_response = process.execute_tools(function_calls)
                for tool_response in tools_response:
                    ClientHandlers().add_message(
                        chat_id=call_info.chat_id,
                        user_id=call_info.user_id,
                        process_name=call_info.process_name,
                        json_message=tool_response,
                    )
        # TODO: Check if we need to retrigger the process.
        # if is_active then request_response().

    except Exception as e:
        logger.error(f"Error in process_response: {e}")


# TODO: Split into Assistant - System.
def get_process(process_name: str, user_id: str, chat_id: str) -> Process:
    if process_name == Assistant.get_process_name():
        return Assistant(user_id=user_id, chat_id=chat_id)
    elif process_name == UserThoughtGenerator.get_process_name():
        return UserThoughtGenerator(user_id=user_id, chat_id=chat_id)
    elif process_name == UserContextManager.get_process_name():
        return UserContextManager(user_id=user_id, chat_id=chat_id)
    elif process_name == UserDataStorageManager.get_process_name():
        return UserDataStorageManager(user_id=user_id, chat_id=chat_id)
    # TODO: Implement me after splitting Assistant - System.
    elif "system":
        pass
    else:
        raise Exception("Unknown process name.")


# TODO: Can have multiple tools.
@celery_app.task(name="system.process_tool_feedback")
def process_tool_feedback(tool_name: str, feedback: str, call_info: CallInfo):
    pass
