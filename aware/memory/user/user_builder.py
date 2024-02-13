from aware.agent.agent_builder import AgentBuilder
from aware.data.database.client_handlers import ClientHandlers
from aware.data.database.data import get_topics
from aware.memory.memory_manager import MemoryManager
from aware.memory.user.user_data import UserData
from aware.utils.logger.file_logger import FileLogger


class UserBuilder:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.logger = FileLogger("user_builder")

    def initialize_user(self, user_name: str, api_key: str):
        # Create user on Weaviate
        try:
            memory_manager = MemoryManager(user_id=self.user_id, logger=self.logger)
            memory_manager.create_user(user_id=self.user_id, user_name=user_name)
        except Exception as e:
            self.logger.error(f"Error while creating weaviate user: {e}")
            raise e
        try:
            assistant_name = "aware"  # TODO: GET FROM SUPABASE!
            AgentBuilder(user_id=self.user_id).initialize_user_agents(
                assistant_name=assistant_name
            )
            ClientHandlers().set_user_data(
                UserData(user_id=self.user_id, user_name=user_name, api_key=api_key)
            )

            # Create initial user topics TODO: Refactor, verify if needed!
            topics_data = get_topics()
            if topics_data is None:
                self.logger.error("DEBUG - No topics data")
                raise Exception("No topics data")
            self.logger.info(f"DEBUG - Got topics data: {topics_data}")
            for topic_name, topic_description in topics_data.items():
                ClientHandlers().create_topic(
                    self.user_id, topic_name, topic_description
                )

        except Exception as e:
            self.logger.error(f"Error while initializing user: {e}")
            raise e
