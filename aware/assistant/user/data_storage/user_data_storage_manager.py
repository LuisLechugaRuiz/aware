from aware.agent.process import Process
from aware.assistant.user.data_storage.user_data_storage_manager_tools import (
    UserDataStorageTools,
)
from aware.utils.logger.file_logger import FileLogger


class UserDataStorageManager(Process):
    def __init__(self, user_id: str, chat_id: str):
        super().__init__(
            user_id=user_id,
            chat_id=chat_id,
            agent_name="User Data Storage Manager",
            run_remote=False,
            tools=UserDataStorageTools(user_id=user_id, chat_id=chat_id),
            module_name="assistant",
        )

    @classmethod
    def get_process_name(self):
        return "user_data_storage_manager"

    # TODO: REMOVE AS IT SHOULD RUN BY EVENT!
    def on_conversation_trim(self):
        """
        Callback function for when a user message is received.
        Returns:
            None
        """
        log = FileLogger("migration_tests", should_print=True)
        log.info("Assistant received message")
        self.request_response()
