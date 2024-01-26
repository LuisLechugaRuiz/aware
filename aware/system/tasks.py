from openai.types.chat import ChatCompletionMessage


from aware.assistant.assistant import Assistant
from aware.data.database.client_handlers import ClientHandlers
from aware.chat.call_info import CallInfo
from aware.chat.conversation_schemas import AssistantMessage, ToolCalls
from aware.process.process import Process
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

        process = Process(user_id=call_info.user_id, process_id=call_info.process_id)
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
            user_id=call_info.user_id,
            process_id=call_info.process_id,
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
                        user_id=call_info.user_id,
                        process_id=call_info.process_id,
                        json_message=tool_response,
                    )
        # TODO: Check if we need to retrigger the process.
        # if is_active then request_response().

    except Exception as e:
        logger.error(f"Error in process_response: {e}")


# TODO: Can have multiple tools.
@celery_app.task(name="system.process_tool_feedback")
def process_tool_feedback(tool_name: str, feedback: str, call_info: CallInfo):
    pass
