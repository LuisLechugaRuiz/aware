from pathlib import Path
import glob
import os
import importlib.util
import inspect
from typing import Dict, Optional, Type

from aware.tools.tools import Tools


class ToolsRegistry:
    _instance: Optional["ToolsRegistry"] = None
    tools: Dict[str, Type[Tools]]

    def __new__(cls, tools_folders: Optional[list[str]] = None):
        if cls._instance is None:
            cls._instance = super(ToolsRegistry, cls).__new__(cls)
            cls._instance.tools = {}
            if tools_folders is not None:
                cls._instance.register_tools(tools_folders)
        return cls._instance

    def register_tools(self, tools_folders: list[str]):
        base_path = Path(__file__).parent

        for tools_folder in tools_folders:
            full_path = base_path / tools_folder
            python_files = glob.glob(str(full_path / "*.py"))
            python_files = [file for file in python_files if "__init__" not in file]

            for file_path in python_files:
                module_name = os.path.splitext(os.path.basename(file_path))[0]
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, Tools) and obj is not Tools:
                        self.tools[name] = obj

    def get_tools(self, tools_name: str) -> Optional[Type[Tools]]:
        return self.tools.get(tools_name)
