import logging
import os

from aware.permanent_storage.permanent_storage import get_permanent_storage_path
from aware.utils.logger.file_logger import FileLogger


class ProcessLogger:
    def __init__(self, user_id: str, agent_name: str, process_name: str):
        self.base_path = os.path.join(
            get_permanent_storage_path(), "logs", user_id, agent_name, process_name
        )
        os.makedirs(self.base_path, exist_ok=True)  # Ensure the base directory exists

    def get_logger(self, file_name, should_print=True, level=logging.NOTSET):
        # Create a full path for the new log file within the process_name folder
        log_file_path = os.path.join(self.base_path, f"{file_name}.log")

        # Return a new FileLogger instance for the specified log file
        return FileLogger(log_file_path, should_print, level)
