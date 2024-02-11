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

    def get_user_data(self) -> UserData:
        redis_handler = ClientHandlers().get_redis_handler()
        supabase_handler = ClientHandlers().get_supabase_handler()
        user_data = redis_handler.get_user_data(self.user_id)

        if user_data is None:
            self.logger.info("User data not found in Redis")
            # Fetch user profile from Supabase
            user_profile = supabase_handler.get_user_profile(self.user_id)
            if user_profile is None:
                raise Exception("User profile not found")

            if not user_profile["initialized"]:
                try:
                    self.initialize_user(user_name=user_profile["display_name"])
                    user_profile["initialized"] = True
                    supabase_handler.update_user_profile(self.user_id, user_profile)
                except Exception as e:
                    self.logger.error(f"Error while initializing user: {e}")
                    raise e

            # Store user data in redis
            user_data = UserData(
                user_id=self.user_id,
                user_name=user_profile["display_name"],
                api_key=user_profile["openai_api_key"],
            )
            redis_handler.set_user_data(user_data)
        else:
            self.logger.info("User data found in Redis")

        return user_data

    def initialize_user(self, user_name: str):
        # Create user on Weaviate
        try:
            memory_manager = MemoryManager(user_id=self.user_id, logger=self.logger)
            result = memory_manager.create_user(
                user_id=self.user_id, user_name=user_name
            )
        except Exception as e:
            self.logger.error(f"Error while creating weaviate user: {e}")
            raise e
        if result.error:
            self.logger.info(
                f"DEBUG - error creating weaviate user result: {result.error}"
            )
        else:
            self.logger.info(
                f"DEBUG - success creating weaviate user result: {result.data}"
            )
        try:
            assistant_name = "aware"  # TODO: GET FROM SUPABASE!
            AgentBuilder(
                user_id=self.user_id, client_handlers=self
            ).initialize_user_agents(assistant_name=assistant_name)

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
            self.logger.error(f"Error while updating agent profile: {e}")
            raise e
