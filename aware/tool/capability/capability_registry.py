import importlib.util
import inspect
import os
from pathlib import Path
from typing import Dict, List, Optional, Type

from aware.database.weaviate.memory_manager import MemoryManager
from aware.process.process_ids import ProcessIds

# TODO: split capability - tool with own CapabilityDatabaseHandler?
from aware.tools.capability.capability import Capability
from aware.tools.database.tool_database_handler import ToolDatabaseHandler

from aware.utils.logger.file_logger import FileLogger


class CapabilityRegistry:
    _instance: Optional["CapabilityRegistry"] = None
    process_ids: ProcessIds
    capabilities: Dict[str, Type[Capability]]
    logger: FileLogger

    def __new__(cls, capabilities_folders: Optional[List[str]] = None):
        if cls._instance is None:
            cls._instance = super(CapabilityRegistry, cls).__new__(cls)
            cls._instance.capabilities = {}
            cls._instance.logger = FileLogger("capability_registry")
            if capabilities_folders is not None:
                cls._instance.register_capabilites(capabilities_folders)
        return cls._instance

    def register_capabilites(self, capabilities_folders: List[str]):
        base_path = Path(__file__).parent

        for capabilities_folder in capabilities_folders:
            full_path = base_path / capabilities_folder
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
                    if issubclass(obj, Capability) and obj is not Capability:
                        self.logger.info(f"Registering capability: {name}")
                        self.capabilities[name] = obj

                # Store capability in memory
                memory_manager = MemoryManager(
                    user_id=self.process_ids.user_id, logger=self.logger
                )
                memory_manager.store_capability(
                    user_id=self.process_ids.user_id,
                    name=name,
                    description=obj.get_description(),
                )
                ToolDatabaseHandler().create_capability(
                    process_ids=self.process_ids, capability_name=name
                )

    def get_capability(self, capability_name: str) -> Optional[Type[Capability]]:
        return self.capabilities.get(capability_name)
