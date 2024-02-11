from openai.types.chat import ChatCompletionMessage

from aware.chat.call_info import CallInfo
from aware.chat.conversation_schemas import (
    AssistantMessage,
    ToolCalls,
)
from aware.data.database.client_handlers import ClientHandlers
from aware.process.process_ids import ProcessIds
from aware.process.process_handler import ProcessHandler
from aware.server.celery_app import celery_app
from aware.utils.logger.file_logger import FileLogger


# ENTRY POINT!
@celery_app.task(name="server.preprocess")
def preprocess(process_ids_str: str):
    process_ids = ProcessIds.from_json(process_ids_str)

    ClientHandlers().add_active_process(process_ids.process_id)
    process = ClientHandlers().get_process(process_ids.process_id)
    process.preprocess()


@celery_app.task(name="server.postprocess")
def postprocess(response_str: str, call_info_str: str):
    # we need to check if have tool_calls at the processes
    logger = FileLogger("migration_tests")
    logger.info(f"Task process_response started with message: {response_str}")

    try:
        # 1. Get process.
        call_info = CallInfo.from_json(call_info_str)

        process = ClientHandlers().get_process(call_info.process_ids.process_id)
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
                process.finish_process()

        logger.info("Adding message to redis and supabase")
        # 3. Upload message to Supabase and Redis.
        ProcessHandler().add_message(
            process_ids=call_info.process_ids, message=new_message
        )

        logger.info("Getting function calls")
        # 4. Get function calls
        if tool_calls:
            function_calls = process.get_function_calls(tool_calls)
            if process.should_run_remote():
                # TODO: Call supabase real-time client.
                pass
            else:
                logger.info("Executing function calls")
                tools_response = process.execute_tools(function_calls)
                for tool_response in tools_response:
                    ProcessHandler().add_message(
                        process_ids=call_info.process_ids, message=tool_response
                    )

        # 5. Check if agent is running or should be stopped.
        if process.is_sync_request_scheduled():
            logger.info(
                f"Sync request scheduled, process: {call_info.process_ids}, waiting for response."
            )
            return

        ProcessHandler().step(
            process_ids=call_info.process_ids,
            is_process_finished=process.is_process_finished(),
        )

    except Exception as e:
        logger.error(f"Error in process_response: {e}")


# TODO: Can have multiple tools.
@celery_app.task(name="server.process_tool_feedback")
def process_tool_feedback(tool_name: str, feedback: str, call_info: CallInfo):
    pass
