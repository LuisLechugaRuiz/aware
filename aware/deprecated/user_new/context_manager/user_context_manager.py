from aware.agent.process import Process
from aware.system.context_manager.context_manager_tools import (
    ContextManagerTools,
)
from aware.utils.logger.file_logger import FileLogger


class UserContextManager(Process):
    def __init__(self, user_id: str, process_id: str):
        super().__init__(
            user_id=user_id,
            process_id=process_id,
            agent_name="User Context Manager",
            run_remote=False,
            tools=ContextManagerTools(user_id=user_id, process_id=process_id),
            module_name="assistant",
        )

    @classmethod
    def get_process_name(self):
        return "user_context_manager"
