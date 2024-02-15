from openai.types.chat import ChatCompletionMessage

from aware.chat.call_info import CallInfo
from aware.chat.conversation_schemas import (
    AssistantMessage,
    ToolCalls,
)
from aware.process.process_handler import ProcessHandler
from aware.process.process import Process
from aware.process.process_ids import ProcessIds
from aware.server.celery_app import app
from aware.utils.logger.file_logger import FileLogger


# ENTRY POINT!
@app.task(name="server.preprocess")
def preprocess(process_ids_str: str):
    logger = FileLogger("server_tasks")
    logger.info(f"Task preprocess started with message: {process_ids_str}")
    try:
        process_ids = ProcessIds.from_json(process_ids_str)
        process = Process(process_ids)
        process.preprocess()
    except Exception as e:
        logger.error(f"Error in preprocess: {e}")


@app.task(name="server.postprocess")
def postprocess(response_str: str, call_info_str: str):
    # we need to check if have tool_calls at the processes
    logger = FileLogger("server_tasks")
    logger.info(f"Task postprocess started with message: {response_str}")

    try:
        # 1. Get process.
        call_info = CallInfo.from_json(call_info_str)
        process = Process(call_info.process_ids)

        # 2. Reconstruct response.
        openai_response = ChatCompletionMessage.model_validate_json(response_str)
        tool_calls = openai_response.tool_calls
        if tool_calls is not None:
            new_message = ToolCalls.from_openai(
                assistant_name=call_info.name,
                tool_calls=openai_response.tool_calls,
            )
        else:
            tool_calls = [process.get_default_tool_call(openai_response.content)]
            if tool_calls is not None:
                new_message = ToolCalls.from_openai(
                    assistant_name=call_info.name,
                    tool_calls=tool_calls,
                )
            else:
                new_message = AssistantMessage(
                    name=call_info.name, content=openai_response.content
                )
                process.finish_process()

        logger.info("Adding message to redis and supabase")
        # 3. Upload message to Supabase and Redis.
        process_handler = ProcessHandler()
        process_handler.add_message(
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
                    process_handler.add_message(
                        process_ids=call_info.process_ids, message=tool_response
                    )

        # 5. Check if agent is running or should be stopped.
        if process.is_sync_request_scheduled():
            logger.info(
                f"Sync request scheduled, process: {call_info.process_ids}, waiting for response."
            )
            return

        process_handler.step(
            process_ids=call_info.process_ids,
            is_process_finished=process.is_process_finished(),
        )

    except Exception as e:
        logger.error(f"Error in process_response: {e}")


# TODO: Can have multiple tools.
@app.task(name="server.process_tool_feedback")
def process_tool_feedback(tool_name: str, feedback: str, call_info: CallInfo):
    pass
