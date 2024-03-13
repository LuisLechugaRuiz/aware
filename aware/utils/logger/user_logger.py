import logging
import os

from aware.permanent_storage.permanent_storage import get_permanent_storage_path
from aware.utils.logger.file_logger import FileLogger


class UserLogger:
    def __init__(self, user_id: str):
        self.base_path = os.path.join(
            get_permanent_storage_path(), "logs", user_id, "user_logs"
        )
        os.makedirs(self.base_path, exist_ok=True)  # Ensure the base directory exists

    def get_logger(self, file_name, should_print=True, level=logging.NOTSET):
        # Return a new FileLogger instance for the specified log file
        return FileLogger(file_name, should_print, level)
