from pathlib import Path

# import glob
import os
import importlib.util
import inspect
from typing import Dict, Optional, Type

from aware.data.database.client_handlers import ClientHandlers
from aware.memory.memory_manager import MemoryManager
from aware.process.process_ids import ProcessIds
from aware.tools.tools import Tools
from aware.utils.logger.file_logger import FileLogger


class ToolsRegistry:
    _instance: Optional["ToolsRegistry"] = None
    process_ids: ProcessIds
    tools: Dict[str, Type[Tools]]
    logger: FileLogger

    def __new__(cls, user_id: str, tools_folders: Optional[list[str]] = None):
        if cls._instance is None:
            cls._instance = super(ToolsRegistry, cls).__new__(cls)
            cls._instance.tools = {}
            cls._instance.user_id = user_id
            cls._instance.logger = FileLogger("tools_registry")
            if tools_folders is not None:
                cls._instance.register_tools(tools_folders)
        return cls._instance

    def register_tools(self, tools_folders: list[str]):
        base_path = Path(__file__).parent

        for tools_folder in tools_folders:
            full_path = base_path / tools_folder
            python_files = list(
                full_path.rglob("*.py")
            )  # Use rglob for recursive search
            python_files = [
                str(file) for file in python_files if "__init__" not in file.name
            ]

            for file_path in python_files:
                module_name = os.path.splitext(os.path.basename(file_path))[0]
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, Tools) and obj is not Tools:
                        self.logger.info(f"Registering tool: {name}")
                        self.tools[name] = obj

                # Store tools in memory
                memory_manager = MemoryManager(
                    user_id=self.process_ids.user_id, logger=self.logger
                )
                memory_manager.store_capability(
                    user_id=self.process_ids.user_id,
                    name=name,
                    description=obj.get_description(),
                )
                # TODO: Remove dependencies to ClientHandlers
                ClientHandlers().create_capability(
                    process_ids=self.process_ids, capability_name=name
                )

    def get_tools(self, tools_name: str) -> Optional[Type[Tools]]:
        return self.tools.get(tools_name)
