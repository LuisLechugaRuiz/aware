from dataclasses import dataclass
import json
from typing import Any, Dict
from pathlib import Path

from aware.config import get_internal_processes_path


@dataclass
class ProcessConfigFiles:
    config: Dict[str, Any]
    state_machine: Dict[str, Any]


class ProcessesConfigLoader:
    def __init__(self):
        self.internal_processes_path = get_internal_processes_path()

    @staticmethod
    def get_file(file_path: Path) -> Dict[str, Any]:
        if file_path.exists():
            with open(file_path, "r") as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"File not found: {file_path}")

    def get_process_files(self, process_name: str) -> ProcessConfigFiles:
        process_path = self.internal_processes_path / process_name
        config_files = ['config.json', 'state_machine.json']
        data = {}

        for file_name in config_files:
            file_path = process_path / file_name
            try:
                data[file_name.split('.')[0]] = self.get_file(file_path)
            except FileNotFoundError as e:
                print(f"Warning: {e}")

        return ProcessConfigFiles(**data)

    def get_all_processes_files(self) -> Dict[str, ProcessConfigFiles]:
        process_config = {}

        for process_folder in [f for f in self.internal_processes_path.iterdir() if f.is_dir()]:
            process_name = process_folder.name
            process_folder[process_name] = self.get_process_files(process_name)

        return process_config
