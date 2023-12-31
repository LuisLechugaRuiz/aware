import json
import threading
from typing import Optional

from aware.utils.logger.file_logger import FileLogger
from aware.utils.helpers import get_current_date


class JSONManager:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lock = threading.RLock()

    def load_from_json(self):
        with self.lock:
            try:
                with open(self.file_path, "r") as file:
                    return json.load(file)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error loading JSON from {self.file_path}: {e}")
                return None

    def update(self, field: str, data: str, logger: Optional[FileLogger] = None):
        with self.lock:
            json_data = self.load_from_json()
            if json_data is not None:
                json_data[field] = data
                date = json_data.get("date", None)
                if date is not None:
                    json_data["date"] = get_current_date()
                try:
                    with open(self.file_path, "w") as file:
                        json.dump(json_data, file, indent=4)
                except OSError as e:
                    if logger is not None:
                        logger.error(
                            f"Error writing to {self.file_path}: {e}",
                            should_print_local=True,
                        )
                    else:
                        print(f"Error writing to {self.file_path}: {e}")
            else:
                if logger is not None:
                    logger.error(
                        f"Error updating {field} in {self.file_path}, json manager wrong construction",
                        should_print_local=True,
                    )
                else:
                    print(
                        f"Error updating {field} in {self.file_path}, json manager wrong construction"
                    )
