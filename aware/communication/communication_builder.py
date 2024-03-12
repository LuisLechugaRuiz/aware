from typing import Dict, List

from aware.agent.agent_communication import AgentCommunicationConfig
from aware.communication.protocols import (
    ActionClientConfig,
    ActionServiceConfig,
    RequestClientConfig,
    RequestServiceConfig
)
from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)
from aware.communication.primitives import (
    ActionConfig,
    EventConfig,
    RequestConfig,
    TopicConfig,
)
from aware.communication.primitives.primitives_config import CommunicationPrimitivesConfig
from aware.communication.protocols.database.protocols_database_handler import (
    ProtocolsDatabaseHandler,
)


# TODO: We should fetch from the specific config of the use-case that we are running.
#  - For this we should include organization on supabase so we can get the specific organization config on server.
#  - TODO: For now just by user_id? This implies specific agents for each user, we can add org in the future.
class CommunicationBuilder:
    def __init__(self, user_id: str):
        self.user_id = user_id

        self.action_clients: Dict[str, ActionClientConfig] = {}
        self.action_services: Dict[str, ActionServiceConfig] = {}

        self.request_clients: Dict[str, RequestClientConfig] = {}
        self.request_services: Dict[str, RequestServiceConfig] = {}

        self.primitives_database_handler = PrimitivesDatabaseHandler()
        self.protocols_database_handler = ProtocolsDatabaseHandler()

    def end_setup(self):
        # Create clients and services
        for main_process_id, action_config in self.action_services.items():
            self.create_action_service(
                main_process_id=main_process_id, service_config=action_config
            )

        for main_process_id, action_config in self.action_clients.items():
            self.create_action_client(
                main_process_id=main_process_id, client_config=action_config
            )

        for main_process_id, service_config in self.request_services.items():
            self.create_request_service(
                main_process_id=main_process_id, service_config=service_config
            )

        for main_process_id, client_config in self.request_clients.items():
            self.create_request_client(
                main_process_id=main_process_id, client_config=client_config
            )

        self._reset()

    def setup_communications(self, communication_primitives_config: CommunicationPrimitivesConfig):
        self._reset()

        self.create_actions(communication_primitives_config.action_configs)
        self.create_events(communication_primitives_config.event_configs)
        self.create_requests(communication_primitives_config.request_configs)
        self.create_topics(communication_primitives_config.topic_configs)

    def setup_agent(
        self, main_process_id: str, communications_config: AgentCommunicationConfig
    ):
        # Topic and events are pub/sub, we can create them directly instead of waiting for all services to exist.
        self.create_topic_communications(
            process_ids=main_process_id, communications_config=communications_config
        )
        self.create_event_communications(
            process_ids=main_process_id, communications_config=communications_config
        )
        # Save clients and servers until end_setup
        self.action_clients[main_process_id] = communications_config.action_clients
        self.action_services[main_process_id] = communications_config.action_services

        self.request_clients[main_process_id] = communications_config.request_clients
        self.request_services[main_process_id] = communications_config.request_services

    def _reset(self):
        # Reset clients and services
        self.request_clients = {}
        self.request_services = {}

    # TODO: We should split between type and message.
    def create_events(self, event_configs: List[EventConfig]):
        for event_config in event_configs:
            self.primitives_database_handler.create_event_type(
                publisher_id=self.user_id,
                event_name=event_config.name,
                event_description=event_config.description,
                message_format=event_config.message_format,
            )

    # TODO: Same than for event, we should split between type and message.
    def create_topics(self, topic_configs: List[TopicConfig]):
        for topic_config in topic_configs:
            self.primitives_database_handler.create_topic(
                user_id=self.user_id,
                topic_name=topic_config.name,
                topic_description=topic_config.description,
                message_format=topic_config.message_format,
            )

    def create_actions(self, action_configs: List[ActionConfig]):
        for action_config in action_configs:
            self.primitives_database_handler.create_action_type(
                user_id=self.user_id,
                action_name=action_config.name,
                request_format=action_config.request_format,
                feedback_format=action_config.feedback_format,
                response_format=action_config.response_format,
            )

    def create_requests(self, request_configs: List[RequestConfig]):
        for request_config in request_configs:
            self.primitives_database_handler.create_request_type(
                user_id=self.user_id,
                request_name=request_config.name,
                request_format=request_config.request_format,
                response_format=request_config.response_format,
            )

    def create_action_service(self, main_process_id: str, service_config: ActionServiceConfig):
        self.protocols_database_handler.create_action_service(
            user_id=self.user_id,
            process_id=main_process_id,
            service_name=service_config.service_name,
            service_description=service_config.service_description,
            action_name=service_config.action_name,
        )

    def create_action_client(self, main_process_id: str, client_config: ActionClientConfig):
        self.protocols_database_handler.create_action_client(
            user_id=self.user_id,
            process_id=main_process_id,
            service_name=client_config.service_name,
        )

    def create_request_client(self, main_process_id: str, client_config: RequestClientConfig):
        self.protocols_database_handler.create_request_client(
            user_id=self.user_id,
            process_id=main_process_id,
            service_name=client_config.service_name,
        )

    def create_request_service(
        self, main_process_id: str, service_config: RequestServiceConfig
    ):
        self.protocols_database_handler.create_request_service(
            user_id=self.user_id,
            process_id=main_process_id,
            service_name=service_config.service_name,
            service_description=service_config.service_description,
            request_name=service_config.request_name,
            tool_name=service_config.tool_name,  # This implies that the agent managing the service have access to the tool.. verify.
        )

    def create_event_communications(
        self, main_process_id: str, communications_config: AgentCommunicationConfig
    ):
        # Events are always external, no public/private for now.
        # Processes should ONLY subscribe as the publishers should be external!
        for event_subscriber in communications_config.event_subscribers:
            self.protocols_database_handler.create_event_subscriber(
                user_id=self.user_id,
                process_id=main_process_id,
                event_name=event_subscriber.event_name,
            )

    def create_topic_communications(
        self, main_process_id: str, communications_config: AgentCommunicationConfig
    ):
        for topic_publisher in communications_config.topic_publishers:
            self.protocols_database_handler.create_topic_publisher(
                user_id=self.user_id,
                process_id=main_process_id,
                topic_name=topic_publisher.topic_name,
            )

        for topic_subscriber in communications_config.topic_subscribers:
            self.protocols_database_handler.create_topic_subscriber(
                user_id=self.user_id,
                process_id=main_process_id,
                topic_name=topic_subscriber.topic_name,
            )
