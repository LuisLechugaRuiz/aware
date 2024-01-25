from aware.agent.process import Process
from aware.system.context_manager.context_manager_tools import (
    ContextManagerTools,
)


class ContextManager(Process):
    def __init__(self, user_id: str, process_id: str):
        super().__init__(
            user_id=user_id,
            process_id=process_id,
            agent_name="Context Manager",
            run_remote=False,
            tools=ContextManagerTools(user_id=user_id, process_id=process_id),
            module_name="system",
        )

    @classmethod
    def get_process_name(self):
        return "context_manager"
