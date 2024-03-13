from typing import Dict, List

from aware.database.client_handlers import ClientHandlers
from aware.utils.logger.file_logger import FileLogger  # TODO: use agent logger?
from aware.team.database.team_redis_handler import TeamRedisHandler
from aware.team.database.team_supabase_handler import TeamSupabaseHandler


class TeamDatabaseHandler:
    def __init__(self):
        self.redis_handler = TeamRedisHandler(
            client=ClientHandlers().get_redis_client()
        )
        self.supabase_handler = TeamSupabaseHandler(
            client=ClientHandlers().get_supabase_client()
        )
        self.logger = FileLogger("process_agent_handler")

    def get_agent(self, team_id: str):

    # TODO: Implement me.
    def get_team_data(self, team_data: str):