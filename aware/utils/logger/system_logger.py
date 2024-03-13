import os

from aware.permanent_storage.permanent_storage import get_permanent_storage_path
from aware.utils.logger.file_logger import FileLogger


class SystemLogger(FileLogger):
    def __init__(self, module_name: str):
        self.base_path = os.path.join(
            get_permanent_storage_path(), "logs", "system_logs"
        )
        os.makedirs(self.base_path, exist_ok=True)  # Ensure the base directory exists
        log_path = os.path.join(self.base_path, f"{module_name}.log")
        super().__init__(log_path, True)
