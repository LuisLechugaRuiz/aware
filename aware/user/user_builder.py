from aware.agent.agent_builder import AgentBuilder
from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)
from aware.database.weaviate.memory_manager import MemoryManager
from aware.user.user_data import UserData
from aware.user.database.user_database_handler import UserDatabaseHandler
from aware.utils.logger.file_logger import FileLogger


class UserBuilder:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.primitives_database_handler = PrimitivesDatabaseHandler()
        self.logger = FileLogger("user_builder")

    def initialize_user(self, user_name: str, api_key: str):
        self.logger.info(
            f"Initializing user: {user_name} with id: {self.user_id} and api_key: {api_key}"
        )
        try:
            # Create user on Weaviate
            memory_manager = MemoryManager(user_id=self.user_id, logger=self.logger)
            memory_manager.create_user(user_id=self.user_id, user_name=user_name)
        except Exception as e:
            self.logger.error(f"Error while creating weaviate user: {e}")
            raise e
        try:
            # Set user data
            UserDatabaseHandler().set_user_data(
                UserData(user_id=self.user_id, user_name=user_name, api_key=api_key)
            )
            # Set initial user agents
            assistant_name = "aware"  # TODO: GET FROM SUPABASE!
            config_template_name = "autonomous" # TODO: GET FROM SUPABASE!
            AgentBuilder(user_id=self.user_id).initialize_user_agents(
                config_template_name=config_template_name, user_id=self.user_id, assistant_name=assistant_name
            )

        except Exception as e:
            self.logger.error(f"Error while initializing user: {e}")
            raise e
