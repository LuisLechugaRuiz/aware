from aware.chat.call_info import CallInfo
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
        call_info = CallInfo.from_json(call_info_str)
        process = Process(call_info.process_ids)
        process.postprocess(response_str=response_str)
    except Exception as e:
        logger.error(f"Error in process_response: {e}")


# TODO: Can have multiple tools.
@app.task(name="server.process_tool_feedback")
def process_tool_feedback(tool_name: str, feedback: str, call_info: CallInfo):
    pass
