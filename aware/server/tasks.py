from openai.types.chat import ChatCompletionMessage

from aware.chat.call_info import CallInfo
from aware.chat.conversation_schemas import AssistantMessage, ToolCalls
from aware.data.database.client_handlers import ClientHandlers
from aware.process.process import Process
from aware.process.process_ids import ProcessIds
from aware.server.celery_app import celery_app
from aware.utils.logger.file_logger import FileLogger


# ENTRY POINT!
@celery_app.task(name="server.preprocess")
def preprocess(process_ids_str: str):
    process_ids = ProcessIds.from_json(process_ids_str)

    ClientHandlers().add_active_process(process_ids.process_id)

    process_data = ClientHandlers().get_process_data(process_ids)
    Process(process_data=process_data).preprocess()


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
        if process.is_request_scheduled():
            logger.info(
                f"Request scheduled, process: {call_info.process_ids}, waiting for response."
            )
            return

        if process.is_running():
            preprocess.delay(call_info.process_ids.to_json())
        else:
            # Check if has requests and schedule the newest one or just stop it!
            new_request = ClientHandlers().get_request(call_info.process_ids)
            if new_request is None:
                ClientHandlers().remove_active_process(call_info.process_ids)
            else:
                # Schedule it again to complete new request.
                preprocess.delay(call_info.process_ids.to_json())

    except Exception as e:
        logger.error(f"Error in process_response: {e}")


# TODO: Can have multiple tools.
@celery_app.task(name="server.process_tool_feedback")
def process_tool_feedback(tool_name: str, feedback: str, call_info: CallInfo):
    pass


@celery_app.task(name="server.set_request_completed")
def set_request_completed(request_id: str, response: str):
    # TODO: Implement me.
    # 1. Get the client id from request_id.
    redis_handler = ClientHandlers().get_redis_handler()
    request = redis_handler.get_request(request_id)
    # 2. Add the response as the response of last tool_call!!
    last_message = ClientHandlers().get_last_message(
        process_id=request.client_process_id,
    )
    # Should be of type:
    # self.role = "tool"
    # self.content = content
    # self.tool_call_id = tool_call_id
    last_message.content = response

    # 3. Schedule client again using preprocess - Remove request from redis?
    # redis_handler.delete_request(request_id)
    agent_id = redis_handler.get_agent_id_by_process_id(request.client_process_id)

    # Now we need to get user_id also....
    # process_ids = ProcessIds(
    #     user_id=??,
    #     agent_id=agent_id,
    #     process_id=request.client_process_id
    # )
    # preprocess.delay(process_ids.to_json())
