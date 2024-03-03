from typing import Dict, Any

from aware.communication.primitives.database.primitives_database_handler import (
    PrimitivesDatabaseHandler,
)
from aware.communication.protocols.database.protocols_database_handler import (
    ProtocolsDatabaseHandler,
)
from aware.process.process_ids import ProcessIds


class CommunicationBuilder:
    def __init__(self):
        self.clients: Dict[ProcessIds, Dict[str, Any]] = {}
        self.services: Dict[ProcessIds, Dict[str, Any]] = {}
        self.primitives_database_handler = PrimitivesDatabaseHandler()
        self.protocols_database_handler = ProtocolsDatabaseHandler()

    def end_setup(self):
        # Create clients and services
        for process_ids, service_config in self.services.items():
            self.create_request_service(
                process_ids=process_ids, service_config=service_config
            )

        for process_ids, service_name in self.clients.items():
            self.create_request_client(
                process_ids=process_ids, service_name=service_name
            )

        self._reset()

    def setup_communications(self):
        self._reset()

        self.create_agent_events()
        self.create_agent_requests()
        self.create_agent_topics()

    def setup_process(
        self, process_ids: ProcessIds, communications_config: Dict[str, Any]
    ):
        self.create_topic_communications(
            process_ids=process_ids, communications_config=communications_config
        )
        # Save clients and servers until end_setup
        self.clients[process_ids] = communications_config["clients"]
        self.services[process_ids] = communications_config["services"]

    def _reset(self):
        # Reset clients and services
        self.clients = {}
        self.services = {}

    # TODO: This should match the agent creation at AgentBuilder.
    def create_new_agent(
        self, process_ids: ProcessIds, communications_config: Dict[str, Any]
    ):
        self.create_event_communications(
            process_ids=process_ids, communications_config=communications_config
        )
        self.create_topic_communications(
            process_ids=process_ids, communications_config=communications_config
        )
        self.create_request_communications(
            process_ids=process_ids, communications_config=communications_config
        )

    # TODO: Merge this functions with existing create_event_type, create_topic and create_request_type (create_request_messsage?)
    def create_agent_events(self):
        # TODO: Fetch events from agent communications folder at config and create them as public.
        pass

    # # TODO: We should have a dynamic blackboard where events are updated. Events are used to stream external info to specific process! (from now just .json file)
    # def initialize_events(self):
    #     events_data = get_events()
    #     if events_data is None:
    #         self.logger.info("No events.")
    #         return
    #     self.logger.info(f"Got events data: {events_data}")
    #     for event_name, event_description in events_data.items() # TODO: FIX THIS!
    #         self.primitives_database_handler.create_event_type(
    #             self.user_id, event_name, event_description, message_format
    #         )

    # TODO: We should have a dynamic blackboard where topics are updated. Topics are used to share info process to process! (from now just .json file)
    # def initialize_topics(self):
    #     topics_data = get_topics()
    #     if topics_data is None:
    #         self.logger.info("No topics.")
    #         return
    #     self.logger.info(f"Got topics data: {topics_data}")
    #     for topic_name, topic_description in topics_data.items():
    #         self.primitives_database_handler.create_topic(self.user_id, topic_name, topic_description)

    def create_agent_topics(self):
        # TODO: Fetch topics from agent communications folder at config and create them as public.
        pass

    def create_agent_requests(self):
        # TODO: Fetch requests from agent communications folder at config, no need of public or private as is always process to process.
        self.primitives_database_handler.create_request_type(
            user_id,
            request_name,
            request_format,
            response_format,
            feedback_format,
        )
        pass

    def create_request_client(self, process_ids: ProcessIds, service_name: str):
        self.protocols_database_handler.create_request_client(
            user_id=process_ids.user_id,
            process_id=process_ids.process_id,
            service_name=service_name,
        )

    def create_request_service(
        self, process_ids: ProcessIds, service_config: Dict[str, Any]
    ):
        self.protocols_database_handler.create_request_service(
            user_id=process_ids.user_id,
            process_id=process_ids.process_id,
            service_name=service_config["name"],
            service_description=service_config["description"],
            request_name=service_config["request_name"],
            tool_name=service_config.get("tool_name", None),
        )

    def create_event_communications(
        self, process_ids: ProcessIds, communications_config: Dict[str, Any]
    ):
        # Events are always external, no public/private for now.
        # Processes should ONLY subscribe as the publishers should be external!
        event_subscribers = communications_config["event_subscribers"]
        for event_name in event_subscribers:
            self.protocols_database_handler.create_event_subscriber(
                process_ids=process_ids,
                event_name=event_name,
            )

    def create_request_communications(
        self, process_ids: ProcessIds, communications_config: Dict[str, Any]
    ):
        service_config = communications_config["request_services"]
        self.create_request_service(
            process_ids=process_ids, service_config=service_config
        )

        client_name = communications_config["request_clients"]
        self.create_request_client(process_ids=process_ids, service_name=client_name)

    def create_topic_communications(
        self, process_ids: ProcessIds, communications_config: Dict[str, Any]
    ):
        # Create private topics for internal processes.
        # TODO: Fetch the topics from the internal_processes communications folder at config and create them as private using agent_id!

        topic_publishers = communications_config["topic_publishers"]
        for topic_name in topic_publishers:
            self.protocols_database_handler.create_topic_publisher(
                user_id=process_ids.user_id,
                process_id=process_ids.process_id,
                topic_name=topic_name,
            )

        topic_subscribers = communications_config["topic_subscribers"]
        for topic_name in topic_subscribers:
            self.protocols_database_handler.create_topic_subscriber(
                user_id=process_ids.user_id,
                process_id=process_ids.process_id,
                topic_name=topic_name,
            )
