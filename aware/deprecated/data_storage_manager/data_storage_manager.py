from aware.agent.process import Process
from aware.system.data_storage_manager.data_storage_manager_tools import (
    DataStorageManagerTools,
)


class DataStorageManager(Process):
    def __init__(self, user_id: str, process_id: str):
        super().__init__(
            user_id=user_id,
            process_id=process_id,
            run_remote=False,
            tools=DataStorageManagerTools(user_id=user_id, process_id=process_id),
            module_name="system",
        )

    @classmethod
    def get_process_name(self):
        return "data_storage_manager"
