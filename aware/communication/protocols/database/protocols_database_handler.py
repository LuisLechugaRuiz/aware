from typing import Any, Dict, List, Optional, Tuple

from aware.agent.agent_communication import AgentCommunication
from aware.communication.helpers.current_input_metadata import CurrentInputMetadata
from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)
from aware.communication.primitives.interface.input import Input
from aware.communication.primitives import Action, Request, Event
from aware.communication.protocols.interface.input_protocol import InputProtocol
from aware.communication.protocols.database.protocols_redis_handler import (
    ProtocolsRedisHandler,
)
from aware.communication.protocols.database.protocols_supabase_handler import (
    ProtocolSupabaseHandler,
)
from aware.communication.protocols import (
    EventSubscriber,
    EventPublisher,
    TopicPublisher,
    TopicSubscriber,
    RequestClient,
    RequestService,
    ActionClient,
    ActionService,
)
from aware.communication.protocols.action_service import ActionServiceData
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
        self.primitives_database_handler = PrimitivesDatabaseHandler()
        self.logger = FileLogger("protocols_database_handler")

    def delete_current_input(self, process_id: str):
        self.primitives_database_handler.delete_current_input(process_id)

    def get_agent_communication(self, process_id: str) -> AgentCommunication:
        current_input, input_protocol = self.get_current_input(process_id)
        if current_input is None:
            raise Exception(
                "Trying to get communication protocols without current input"
            )

        input_protocol.add_input(current_input)
        agent_communication = AgentCommunication(
            topic_publishers=self.get_topic_publishers(process_id),
            topic_subscribers=self.get_topic_subscribers(process_id),
            action_clients=self.get_action_clients(process_id),
            request_clients=self.get_request_clients(process_id),
            input_protocol=input_protocol,
        )
        return agent_communication

    def get_current_input(
        self, process_id: str
    ) -> Tuple[Optional[Input], Optional[InputProtocol]]:
        current_input_metadata = (
            self.primitives_database_handler.get_current_input_metadata(process_id)
        )
        if current_input_metadata is None:
            return None, None

        if current_input_metadata.input_type == Request.get_type():
            current_input = self.primitives_database_handler.get_request(
                current_input_metadata.input_id
            )
            input_protocol = self.redis_handler.get_request_service(
                current_input_metadata.protocol_id
            )
        elif current_input_metadata.input_type == Action.get_type():
            current_input = self.primitives_database_handler.get_action(
                current_input_metadata.input_id
            )
            input_protocol = self.redis_handler.get_action_service(
                current_input_metadata.protocol_id
            )
        elif current_input_metadata.input_type == Event.get_type():
            current_input = self.primitives_database_handler.get_event(
                current_input_metadata.input_id
            )
            input_protocol = self.redis_handler.get_event_subscriber(
                current_input_metadata.protocol_id
            )
        else:
            raise Exception(f"Unknown input type: {current_input_metadata.input_type}")
        return current_input, input_protocol

    def has_current_input(self, process_id) -> bool:
        current_input_metadata = (
            self.primitives_database_handler.get_current_input_metadata(process_id)
        )
        return current_input_metadata is not None

    def update_highest_prio_input(self, process_id: str) -> bool:
        highest_prio_input: Optional[Input] = None
        current_input_protocol: Optional[InputProtocol] = None

        # Consolidate all services and subscribers into a single iterable
        # TODO: How to get highest priority input without creating all the protocols as they require to have input?
        all_input_protocols: List[InputProtocol] = [
            *self.get_request_services(process_id).values(),
            *self.get_action_services(process_id).values(),
            *self.get_event_subscribers(process_id).values(),
        ]

        # Iterate over all input sources to find the one with the highest priority
        for input_protocol in all_input_protocols:
            new_input = input_protocol.get_highest_priority_input()
            if new_input and (
                highest_prio_input is None
                or new_input.priority > highest_prio_input.priority
            ):
                highest_prio_input = new_input
                current_input_protocol = input_protocol

        if highest_prio_input is None:
            return False

        # Update the current input metadata
        current_input_metadata = CurrentInputMetadata(
            input_type=highest_prio_input.get_type(),
            input_id=highest_prio_input.id,
            protocol_id=current_input_protocol.id,
        )
        self.primitives_database_handler.set_current_input_metadata(
            process_id, current_input_metadata
        )
        return True

    # TODO: Create event subscriber.
    def create_action_client(self, user_id: str, process_id: str, action_name: str):
        action_client = self.supabase_handler.create_action_client(
            user_id=user_id, process_id=process_id, action_name=action_name
        )
        self.redis_handler.create_action_client(action_client=action_client)

    def create_action_service(
        self,
        user_id: str,
        process_id: str,
        service_data: ActionServiceData,
    ):
        action_service = self.supabase_handler.create_action_service(
            user_id=user_id,
            process_id=process_id,
            service_data=service_data,
        )
        self.redis_handler.create_action_service(action_service=action_service)

    def create_event_subscriber(self, user_id: str, process_id: str, event_name: str):
        event_subscriber = self.supabase_handler.create_event_subscriber(
            user_id=user_id, process_id=process_id, event_name=event_name
        )
        self.redis_handler.create_event_subscriber(event_subscriber=event_subscriber)

    def create_request_client(self, user_id: str, process_id: str, service_name: str):
        request_client = self.supabase_handler.create_request_client(
            user_id=user_id, process_id=process_id, service_name=service_name
        )
        self.redis_handler.create_request_client(request_client=request_client)

    def create_request_service(
        self,
        user_id: str,
        process_id: str,
        service_data: RequestServiceData,
    ):
        """Create new service"""
        request_service = self.supabase_handler.create_request_service(
            user_id=user_id,
            process_id=process_id,
            service_data=service_data,
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

    # TODO: Just fetching from redis, should we fallback to supabase?
    def get_event_subscribers_from_type(
        self, event_type_id: str
    ) -> List[EventSubscriber]:
        return self.redis_handler.get_event_subscribers_from_type(event_type_id)

    def get_request_services(self, process_id: str) -> Dict[str, RequestService]:
        return self.redis_handler.get_request_services(process_id)

    def get_request_client(self, request_client_id: str) -> Optional[RequestClient]:
        return self.redis_handler.get_request_client(request_client_id)

    def get_request_clients(self, process_id: str) -> Dict[str, RequestClient]:
        return self.redis_handler.get_request_clients(process_id)

    def get_action_clients(self, process_id: str) -> Dict[str, ActionClient]:
        return self.redis_handler.get_action_clients(process_id)

    def get_action_services(self, process_id: str) -> Dict[str, ActionService]:
        return self.redis_handler.get_action_services(process_id)

    def get_topic_publishers(self, process_id: str) -> Dict[str, TopicPublisher]:
        return self.redis_handler.get_topic_publishers(process_id)

    def get_topic_subscribers(self, process_id: str) -> Dict[str, TopicSubscriber]:
        return self.redis_handler.get_topic_subscribers(process_id)

    def get_topic_subscribers_from_topic(self, topic_id: str) -> List[TopicSubscriber]:
        return self.redis_handler.get_topic_subscribers_from_topic(topic_id)

    def get_event_subscribers(self, process_id: str) -> Dict[str, EventSubscriber]:
        return self.redis_handler.get_event_subscribers(process_id)

    def get_event_publisher(self, publisher_id: str) -> Optional[EventPublisher]:
        return self.redis_handler.get_event_publisher(publisher_id)
