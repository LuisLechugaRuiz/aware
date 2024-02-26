from aware.agent.agent_builder import AgentBuilder

from aware.communications.events import get_events
from aware.communications.topics import get_topics

from aware.data.database.client_handlers import ClientHandlers
from aware.memory.memory_manager import MemoryManager
from aware.memory.user.user_data import UserData
from aware.utils.logger.file_logger import FileLogger


class UserBuilder:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.logger = FileLogger("user_builder")

    def initialize_user(self, user_name: str, api_key: str):
        self.logger.info(
            f"Initializing user: {user_name} with id: {self.user_id} and api_key: {api_key}"
        )
        # Create user on Weaviate
        try:
            memory_manager = MemoryManager(user_id=self.user_id, logger=self.logger)
            memory_manager.create_user(user_id=self.user_id, user_name=user_name)
        except Exception as e:
            self.logger.error(f"Error while creating weaviate user: {e}")
            raise e
        try:
            ClientHandlers().set_user_data(
                UserData(user_id=self.user_id, user_name=user_name, api_key=api_key)
            )
            # TODO: REMOVE THIS! Will be constructed as part of initialize_user_agents.
            self.initialize_events()
            self.initialize_topics()

            assistant_name = "aware"  # TODO: GET FROM SUPABASE!
            AgentBuilder(user_id=self.user_id).initialize_user_agents(
                assistant_name=assistant_name
            )

        except Exception as e:
            self.logger.error(f"Error while initializing user: {e}")
            raise e

    # TODO: We should have a dynamic blackboard where events are updated. Events are used to stream external info to specific process! (from now just .json file)
    def initialize_events(self):
        events_data = get_events()
        if events_data is None:
            self.logger.info("No events.")
            return
        self.logger.info(f"Got events data: {events_data}")
        for event_name, event_description in events_data.items():
            ClientHandlers().create_event_type(
                self.user_id, event_name, event_description
            )

    # TODO: We should have a dynamic blackboard where topics are updated. Topics are used to share info process to process! (from now just .json file)
    def initialize_topics(self):
        topics_data = get_topics()
        if topics_data is None:
            self.logger.info("No topics.")
            return
        self.logger.info(f"Got topics data: {topics_data}")
        for topic_name, topic_description in topics_data.items():
            ClientHandlers().create_topic(self.user_id, topic_name, topic_description)
