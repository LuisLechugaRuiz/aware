import os
import json
from typing import Any, Dict


class JsonLoader:
    def __init__(self, root_dir):
        self.root_dir = root_dir

    def search_files(self, file_names: list) -> Dict[str, Dict[str, Any]]:
        data = {}
        for root, dirs, files in os.walk(self.root_dir):
            # Folder name as a key
            folder_name = os.path.basename(root)
            files_data = {}
            for file_name in file_names:
                if file_name in files:
                    full_path = os.path.join(root, file_name)
                    with open(full_path, "r") as f:
                        config = json.load(f)
                        # Use file name without extension as key for the file data
                        key_name = os.path.splitext(file_name)[0]
                        files_data[key_name] = config
            if files_data:
                data[folder_name] = files_data
        return data
