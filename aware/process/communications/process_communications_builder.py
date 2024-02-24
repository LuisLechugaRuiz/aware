from typing import Dict, Any

from aware.data.database.client_handlers import ClientHandlers
from aware.process.process_ids import ProcessIds


class ProcessCommunicationsBuilder:
    def __init__(self):
        self.clients: Dict[ProcessIds, Dict[str, Any]] = {}
        self.services: Dict[ProcessIds, Dict[str, Any]] = {}

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

    def create_agent_events(self):
        # TODO: Fetch events from agent communications folder at config and create them as public.
        pass

    def create_agent_topics(self):
        # TODO: Fetch topics from agent communications folder at config and create them as public.
        pass

    def create_agent_requests(self):
        # TODO: Fetch requests from agent communications folder at config, no need of public or private as is always process to process.
        pass

    def create_request_client(self, process_ids: ProcessIds, service_name: str):
        ClientHandlers().create_request_client(
            process_ids=process_ids, service_name=service_name
        )

    def create_request_service(
        self, process_ids: ProcessIds, service_config: Dict[str, Any]
    ):
        ClientHandlers().create_request_service(
            process_ids=process_ids,
            name=service_config["name"],
            description=service_config["description"],
            request_name=service_config["request_name"],
            tool_name=service_config["tool_name"],
        )

    def create_event_communications(
        self, process_ids: ProcessIds, communications_config: Dict[str, Any]
    ):
        # Events are always external, no public/private for now.
        # Processes should ONLY subscribe as the publishers should be external!
        event_subscribers = communications_config["event_subscribers"]
        for event_name in event_subscribers:
            ClientHandlers().create_event_subscriber(
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
            ClientHandlers().create_topic_publisher(
                process_ids=process_ids, topic_name=topic_name
            )

        topic_subscribers = communications_config["topic_subscribers"]
        for topic_name in topic_subscribers:
            ClientHandlers().create_topic_subscriber(
                process_ids=process_ids,
                topic_name=topic_name,
            )
