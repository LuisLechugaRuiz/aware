from supabase import Client


from aware.process.process_ids import ProcessIds
from aware.tool.capability.capability import Capability
from aware.utils.logger.file_logger import FileLogger


class ToolSupabaseHandler:
    def __init__(self, client: Client):
        self.client = client
        self.logger = FileLogger("supabase_agent_handler")

    # TODO: we need to enhance capabilities so later team_builder can find the right capability from description and understand the tools!!
    def create_capability(self, process_ids: ProcessIds, capability: Capability):
        self.logger.info(f"Creating capability for process: {process_ids.process_id}")
        response = (
            self.client.table("capabilities")
            .insert(
                {
                    "user_id": process_ids.user_id,
                    "process_id": process_ids.process_id,
                    "name": capability.get_name(),
                    "description": capability.get_description(),
                }
            )
            .execute()
            .data
        )
        self.logger.info(
            f"Capability created for process: {process_ids.process_id}. Response: {response}"
        )
        return Capability(
            process_ids=process_ids,
        )

    # TODO: FILL ME!
    # def create_capability_var():

    # def create_tool():
