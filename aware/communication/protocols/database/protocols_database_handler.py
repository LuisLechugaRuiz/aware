from typing import Dict, List, Optional, Tuple

from aware.communication.communication_protocols import CommunicationProtocols
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
from aware.database.client_handlers import ClientHandlers
from aware.utils.logger.file_logger import FileLogger


# TODO: Implement the current input that is being processed along with the input protocol.
# This will be useful to save it for future iterations and only remove it when is completed.
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

    def get_communication_protocols(self, process_id: str) -> CommunicationProtocols:
        current_input, input_protocol = self.get_current_input()
        if current_input is None:
            current_input, input_protocol = self.get_highest_prio_input(process_id)
            current_input_metadata = CurrentInputMetadata(
                input_type=current_input.get_type(),
                input_id=current_input.id,
                protocol_id=input_protocol.id,
            )
            # Setting here current input metadata. We should probably update input status to processing. (TBD)
            self.redis_handler.set_current_input_metadata(
                process_id, current_input_metadata
            )

        communication_protocols = CommunicationProtocols(
            topic_publishers=self.get_topic_publishers(process_id),
            topic_subscribers=self.get_topic_subscribers(process_id),
            action_clients=self.get_action_clients(process_id),
            request_clients=self.get_request_clients(process_id),
        ).add_input(current_input, input_protocol)

        # TODO: removed to fetch each protocol from database. This means there is no fallback to Supabase...
        # communications = self.redis_handler.get_communication_protocols(
        #     process_id=process_id,
        # )

        # if communications is None:
        #     communications = self.supabase_handler.get_communication_protocols(
        #         process_id=process_id
        #     )
        #     if communications is None:
        #         raise Exception("Process Communications not found on Supabase")

        #     self.redis_handler.set_communications(
        #         process_id=process_id, communications=communications
        #     )
        return communication_protocols

    def get_current_input(
        self, process_id: str
    ) -> Tuple[Optional[Input], Optional[InputProtocol]]:
        current_input_metadata = self.redis_handler.get_current_input_metadata(
            process_id
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

    def get_highest_prio_input(
        self, process_id: str
    ) -> Tuple[Optional[Input], Optional[InputProtocol]]:
        highest_prio_input: Optional[Input] = None
        input_protocol: Optional[InputProtocol] = None

        # Consolidate all services and subscribers into a single iterable
        all_inputs: List[InputProtocol] = [
            *self.get_request_services(process_id).values(),
            *self.get_action_services(process_id).values(),
            *self.get_event_subscribers(process_id).values(),
        ]

        # Function to update the highest priority input and its corresponding protocol
        def update_highest_prio_input(
            new_input: Optional[Input], new_protocol: InputProtocol
        ):
            nonlocal highest_prio_input, input_protocol
            if new_input and (
                highest_prio_input is None
                or new_input.priority > highest_prio_input.priority
            ):
                highest_prio_input = new_input
                input_protocol = new_protocol

        # Iterate over all inputs to find the one with the highest priority
        for input_source in all_inputs:
            new_input = input_source.get_highest_priority_input()
            update_highest_prio_input(new_input, input_source)

        return highest_prio_input, input_protocol

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

    # TODO: Just fetching from redis, should we fallback to supabase?
    def get_event_subscribers_from_type(
        self, event_type_id: str
    ) -> List[EventSubscriber]:
        return self.redis_handler.get_event_subscribers_from_type(event_type_id)

    def get_request_services(self, process_id: str) -> Dict[str, RequestService]:
        self.redis_handler.get_request_services(process_id)

    def get_request_clients(self, process_id: str) -> Dict[str, RequestClient]:
        self.redis_handler.get_request_clients(process_id)

    def get_action_clients(self, process_id: str) -> Dict[str, ActionClient]:
        self.redis_handler.get_action_clients(process_id)

    def get_action_services(self, process_id: str) -> Dict[str, ActionService]:
        self.redis_handler.get_action_services(process_id)

    def get_topic_publishers(self, process_id: str) -> Dict[str, TopicPublisher]:
        self.redis_handler.get_topic_publishers(process_id)

    def get_topic_subscribers(self, process_id: str) -> Dict[str, TopicSubscriber]:
        self.redis_handler.get_topic_subscribers(process_id)

    def get_topic_subscribers_from_topic(self, topic_id: str) -> List[TopicSubscriber]:
        return self.redis_handler.get_topic_subscribers_from_topic(topic_id)

    def get_event_subscribers(self, process_id: str) -> Dict[str, EventSubscriber]:
        self.redis_handler.get_event_subscribers(process_id)

    def get_event_publishers(self, process_id: str) -> Dict[str, EventPublisher]:
        self.redis_handler.get_event_publishers(process_id)