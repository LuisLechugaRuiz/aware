from typing import Optional

from aware.communication.communication_protocols import CommunicationProtocols
from aware.communication.protocols.database.protocols_redis_handler import (
    ProtocolsRedisHandler,
)
from aware.communication.protocols.database.protocols_supabase_handler import (
    ProtocolSupabaseHandler,
)
from aware.database.client_handlers import ClientHandlers
from aware.utils.logger.file_logger import FileLogger


class ProtocolsDatabaseHandler:
    def __init__(self):
        self.redis_handler = ProtocolsRedisHandler(
            client=ClientHandlers().get_redis_client()
        )
        self.supabase_handler = ProtocolSupabaseHandler(
            client=ClientHandlers().get_supabase_client()
        )
        self.logger = FileLogger("protocols_database_handler")

    def get_communication_protocols(self, process_id: str) -> CommunicationProtocols:
        communications = self.redis_handler.get_communication_protocols(
            process_id=process_id,
        )

        if communications is None:
            communications = self.supabase_handler.get_communication_protocols(
                process_id=process_id
            )
            if communications is None:
                raise Exception("Process Communications not found on Supabase")

            self.redis_handler.set_communications(
                process_id=process_id, communications=communications
            )
        return communications

    # TODO: Create event subscriber.
    def create_action_client(self, user_id: str, process_id: str, action_name: str):
        action_client = self.supabase_handler.create_action_client(
            user_id=user_id, process_id=process_id, action_name=action_name
        )
        self.redis_handler.create_action_client(action_client=action_client)

    def create_action_service(self, user_id: str, process_id: str, action_name: str):
        action_service = self.supabase_handler.create_action_service(
            user_id=user_id, process_id=process_id, action_name=action_name
        )
        self.redis_handler.create_action_service(action_service=action_service)

    def create_request_client(self, user_id: str, process_id: str, service_name: str):
        request_client = self.supabase_handler.create_request_client(
            user_id=user_id, process_id=process_id, service_name=service_name
        )
        self.redis_handler.create_request_client(request_client=request_client)

    def create_request_service(
        self,
        user_id: str,
        process_id: str,
        service_name: str,
        service_description: str,
        request_name: str,
        tool_name: Optional[str] = None,
    ):
        """Create new service"""
        request_service = self.supabase_handler.create_request_service(
            user_id=user_id,
            process_id=process_id,
            service_name=service_name,
            service_description=service_description,
            request_name=request_name,
            tool_name=tool_name,
        )
        self.redis_handler.create_request_service(request_service=request_service)

    def create_topic_subscriber(self, user_id: str, process_id: str, topic_name: str):
        topic_subscriber = self.supabase_handler.create_topic_subscriber(
            user_id=user_id,
            process_id=process_id,
            topic_name=topic_name,
        )
        self.redis_handler.create_topic_subscriber(topic_subscriber)
        self.logger.info(
            f"Created subscriber for process_id: {process_id} to topic: {topic_name}"
        )

    def create_topic_publisher(self, user_id: str, process_id: str, topic_name: str):
        topic_publisher = self.supabase_handler.create_topic_publisher(
            user_id=user_id,
            process_id=process_id,
            topic_name=topic_name,
        )
        self.redis_handler.create_topic_publisher(topic_publisher)
        self.logger.info(
            f"Created publisher for process_id: {process_id} to topic: {topic_name}"
        )
