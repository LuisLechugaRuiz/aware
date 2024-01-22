from aware.agent.process import Process
from aware.system.data_storage_manager.data_storage_manager_tools import (
    DataStorageManagerTools,
)


class DataStorageManager(Process):
    def __init__(self, chat_id: str, user_id: str):
        self.chat_id = chat_id
        self.user_id = user_id
        super().__init__(
            user_id=user_id,
            chat_id=chat_id,
            run_remote=False,
            tools=DataStorageManagerTools(user_id=user_id, chat_id=chat_id),
            module_name="system",
        )

    @classmethod
    def get_process_name(self):
        return "data_storage_manager"
