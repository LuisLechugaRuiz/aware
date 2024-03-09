from aware.tool.capability.capability import Capability
from aware.tool.database.tool_redis_handler import (
    ToolRedisHandler,
)
from aware.tool.database.tool_supabase_handler import (
    ToolSupabaseHandler,
)
from aware.process.process_ids import ProcessIds
from aware.database.client_handlers import ClientHandlers
from aware.utils.logger.file_logger import FileLogger  # TODO: use agent logger?


# TODO: Implement me
class ToolDatabaseHandler:
    def __init__(self):
        self.redis_handler = ToolRedisHandler(
            client=ClientHandlers().get_redis_client()
        )
        self.supabase_handler = ToolSupabaseHandler(
            client=ClientHandlers().get_supabase_client()
        )
        self.logger = FileLogger("client_agent_handler")

    def create_capability(self, process_ids: ProcessIds, capability: Capability):
        self.supabase_handler.create_capability(process_ids, capability)
        self.logger.info(
            f"Created capability for process_id: {process_ids.process_id} with name: {capability.get_name()}"
        )

    def create_capability_variable(
        self, capability_id: str, variable_name: str, variable_content: str
    ):
        self.supabase_handler.create_capability_variable(
            capability_id, variable_name, variable_content
        )
        self.redis_handler.create_capability_variable(
            capability_id, variable_name, variable_content
        )
