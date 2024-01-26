from aware.agent.process import Process
from aware.assistant.user_new.data_storage.user_data_storage_manager_tools import (
    UserDataStorageTools,
)
from aware.utils.logger.file_logger import FileLogger


class UserDataStorageManager(Process):
    def __init__(self, user_id: str, process_id: str):
        super().__init__(
            user_id=user_id,
            process_id=process_id,
            agent_name="User Data Storage Manager",
            run_remote=False,
            tools=UserDataStorageTools(user_id=user_id, process_id=process_id),
            module_name="assistant",
        )

    @classmethod
    def get_process_name(self):
        return "user_data_storage_manager"
