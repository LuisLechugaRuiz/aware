from aware.chat.call_info import CallInfo
from aware.process.types.internal_process import InternalProcess
from aware.process.types.main_process import MainProcess
from aware.process.process_ids import ProcessIds
from aware.process.process_data import ProcessType
from aware.process.database.process_database_handler import ProcessDatabaseHandler
from aware.server.celery_app import app
from aware.utils.logger.file_logger import FileLogger


# ENTRY POINT!


# Small factory to build the process depending on type.
def get_process(process_ids: ProcessIds) -> InternalProcess:
    process_data = ProcessDatabaseHandler().get_process_data(
        process_id=process_ids.process_id
    )
    if process_data.type == ProcessType.MAIN:
        return MainProcess(process_ids=process_ids)
    elif process_data.type == ProcessType.INTERNAL:
        return InternalProcess(process_ids=process_ids)
    else:
        raise ValueError(f"Process type not found: {process_data.type}")


@app.task(name="server.preprocess")
def preprocess(process_ids_str: str):
    logger = FileLogger("server_tasks")
    logger.info(f"Task preprocess started with message: {process_ids_str}")
    try:
        process_ids = ProcessIds.from_json(process_ids_str)
        process = get_process(process_ids=process_ids)
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
        process = get_process(process_ids=call_info.process_ids)
        process.postprocess(response_str=response_str)
    except Exception as e:
        logger.error(f"Error in process_response: {e}")


# TODO: Can have multiple tools.
@app.task(name="server.process_tool_feedback")
def process_tool_feedback(tool_name: str, feedback: str, call_info: CallInfo):
    pass
