import logging
import os

from aware.process.database.process_database_handler import ProcessDatabaseHandler
from aware.permanent_storage.permanent_storage import get_permanent_storage_path
from aware.utils.logger.file_logger import FileLogger


class ProcessLogger:
    def __init__(self, process_id: str):
        self.process_database_handler = ProcessDatabaseHandler()
        process_ids = self.process_database_handler.get_process_ids(process_id=process_id)
        process_info = self.process_database_handler.get_process_info(process_ids=process_ids)
        self.base_path = os.path.join(
            get_permanent_storage_path(), "logs", process_ids.user_id, process_info.agent_data.name, process_info.process_data.name
        )
        os.makedirs(self.base_path, exist_ok=True)  # Ensure the base directory exists

    def get_logger(self, file_name, should_print=True, level=logging.NOTSET):
        # Create a full path for the new log file within the process_name folder
        log_file_path = os.path.join(self.base_path, f"{file_name}.log")

        # Return a new FileLogger instance for the specified log file
        return FileLogger(log_file_path, should_print, level)
