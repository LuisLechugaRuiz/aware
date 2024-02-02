import json
from openai.types.chat import ChatCompletionMessage
from typing import Dict

from aware.chat.call_info import CallInfo
from aware.chat.conversation_schemas import AssistantMessage, ToolCalls
from aware.data.database.client_handlers import ClientHandlers
from aware.process.process import Process
from aware.process.process_ids import ProcessIds
from aware.server.celery_app import celery_app
from aware.utils.logger.file_logger import FileLogger


# ENTRY POINT!
# TODO: HOW TO SERIALIZE - DESERIALIZE EXTRA KWARGS?
@celery_app.task(name="server.preprocess")
def preprocess(process_ids_str: str, prompt_kwargs_json: str = "{}"):
    process_ids = ProcessIds.from_json(process_ids_str)
    prompt_kwargs = json.loads(prompt_kwargs_json)

    process_data = ClientHandlers().get_process_data(process_ids)
    Process(process_data=process_data).preprocess(prompt_kwargs=prompt_kwargs)


@celery_app.task(name="server.postprocess")
def postprocess(response_str: str, call_info_str: str):
    # we need to check if have tool_calls at the processes
    logger = FileLogger("migration_tests")
    logger.info(f"Task process_response started with message: {response_str}")

    try:
        # 1. Get process.
        call_info = CallInfo.from_json(call_info_str)
        process_data = ClientHandlers().get_process_data(
            process_ids=call_info.process_ids
        )
        process = Process(process_data=process_data)
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
            user_id=call_info.process_ids.user_id,
            process_id=call_info.process_ids.process_id,
            json_message=new_message,
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
                    ClientHandlers().add_message(
                        user_id=call_info.process_ids.user_id,
                        process_id=call_info.process_ids.process_id,
                        json_message=tool_response,
                    )

        # 5. Check if agent is running or should be stopped.
        if process.is_running():
            prompt_kwargs_json = json.dumps(call_info.prompt_kwargs)
            preprocess.delay(call_info.process_ids.to_json(), prompt_kwargs_json)
        else:
            # Check if has requests and schedule the newest one or just stop it!
            new_request = ClientHandlers().get_request(call_info.process_ids)
            if new_request is None:
                ClientHandlers().stop_process(call_info.process_ids)

    except Exception as e:
        logger.error(f"Error in process_response: {e}")


# TODO: Can have multiple tools.
@celery_app.task(name="system.process_tool_feedback")
def process_tool_feedback(tool_name: str, feedback: str, call_info: CallInfo):
    pass
