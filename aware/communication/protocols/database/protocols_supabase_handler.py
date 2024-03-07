from supabase import Client
from typing import Dict, List, Optional

from aware.communication.communication_protocols import CommunicationProtocols
from aware.communication.protocols import (
    EventSubscriber,
    EventPublisher,
    TopicPublisher,
    TopicSubscriber,
    ActionClient,
    ActionService,
    RequestClient,
    RequestService,
)
from aware.communication.protocols.action_service import ActionServiceData
from aware.communication.protocols.request_service import RequestServiceData
from aware.utils.logger.file_logger import FileLogger


class ProtocolSupabaseHandler:
    def __init__(self, client: Client):
        self.client = client
        self.logger = FileLogger("supabase_handler")

    def create_event_subscriber(
        self, user_id: str, process_id: str, event_name: str
    ) -> EventSubscriber:
        self.logger.info(
            f"Creating subscriber to event_type: {event_name} process: {process_id}"
        )
        response = (
            self.client.rpc(
                "create_event_subscriber",
                {
                    "p_user_id": user_id,
                    "p_process_id": process_id,
                    "p_event_name": event_name,
                },
            )
            .execute()
            .data[0]
        )
        return EventSubscriber(
            id=response["_id"],
            user_id=user_id,
            process_id=process_id,
            event_type_id=response["_event_type_id"],
            event_name=event_name,
            event_description=response["_event_description"],
            event_format=response["_event_format"],
        )

    def create_event_publisher(
        self, user_id: str, process_id: str, event_name: str
    ) -> EventSubscriber:
        self.logger.info(
            f"Creating publisher to event_type: {event_name} process: {process_id}"
        )
        response = (
            self.client.rpc(
                "create_event_publisher",
                {
                    "p_user_id": user_id,
                    "p_process_id": process_id,
                    "p_event_name": event_name,
                },
            )
            .execute()
            .data[0]
        )
        return EventPublisher(
            id=response["_id"],
            user_id=user_id,
            process_id=process_id,
            event_type_id=response["_event_type_id"],
            event_name=event_name,
            event_description=response["_event_description"],
            event_format=response["_event_format"],
        )

    def create_action_client(self, user_id: str, process_id: str, action_name: str):
        self.logger.info(f"Creating client for process: {process_id}")
        response = (
            self.client.rpc(
                "create_action_client",
                {
                    "p_user_id": user_id,
                    "p_process_id": process_id,
                    "p_action_name": action_name,
                },
            )
            .execute()
            .data[0]
        )
        self.logger.info(
            f"Client created for process: {process_id}. Response: {response}"
        )
        return ActionClient(
            id=response["_id"],
            user_id=user_id,
            process_id=process_id,
            process_name=["_process_name"],
            service_id=response["_service_id"],
            service_name=action_name,
            service_description=response["_service_description"],
            request_format=response["_request_format"],
        )

    def create_action_service(self, user_id: str, process_id: str, action_name: str):
        self.logger.info(f"Creating action service {action_name}")
        response = (
            self.client.rpc(
                "create_action_service",
                {
                    "p_user_id": user_id,
                    "p_process_id": process_id,
                    "p_name": action_name,
                },
            )
            .execute()
            .data
        )
        service_data = ActionServiceData(
            service_name=action_name,
            service_description=action_name,
            request_format=response["_request_format"],
            feedback_format=response["_feedback_format"],
            response_format=response["_response_format"],
            tool_name=action_name,
        )
        id = response["_id"]
        self.logger.info(
            f"New service created at supabase. Name: {action_name}, id: {id}"
        )
        return ActionService(
            id=id,
            user_id=user_id,
            process_id=process_id,
            data=service_data,
        )

    def create_request_client(self, user_id: str, process_id: str, service_name: str):
        self.logger.info(f"Creating client for process: {process_id}")
        response = (
            self.client.rpc(
                "create_request_client",
                {
                    "p_user_id": user_id,
                    "p_process_id": process_id,
                    "p_service_name": service_name,
                },
            )
            .execute()
            .data[0]
        )
        self.logger.info(
            f"Client created for process: {process_id}. Response: {response}"
        )
        return RequestClient(
            id=response["_id"],
            user_id=user_id,
            process_id=process_id,
            process_name=["_process_name"],
            service_id=response["_service_id"],
            service_name=service_name,
            service_description=response["_service_description"],
            request_format=response["_request_format"],
        )

    def create_request_service(
        self,
        user_id: str,
        process_id: str,
        service_name: str,
        service_description: str,
        request_name: str,
        tool_name: Optional[str],
    ) -> RequestService:
        self.logger.info(f"Creating request service {service_name}")
        response = (
            self.client.rpc(
                "create_request_service",
                {
                    "p_user_id": user_id,
                    "p_process_id": process_id,
                    "p_name": service_name,
                    "p_description": service_description,
                    "p_request_name": request_name,
                    "p_tool_name": tool_name,
                },
            )
            .execute()
            .data
        )
        service_data = RequestServiceData(
            service_name=service_name,
            service_description=service_description,
            request_format=response["_request_format"],
            feedback_format=response["_feedback_format"],
            response_format=response["_response_format"],
            tool_name=tool_name,
        )
        id = response["_id"]
        self.logger.info(
            f"New service created at supabase. Name: {service_name}, id: {id}"
        )
        return RequestService(
            id=id,
            user_id=user_id,
            process_id=process_id,
            data=service_data,
            requests=[],
        )

    def create_topic_publisher(
        self,
        user_id: str,
        process_id: str,
        topic_name: str,
    ) -> TopicPublisher:
        self.logger.info(f"Creating topic publisher for process {process_id}")
        response = (
            self.client.rpc(
                "create_topic_publisher",
                {
                    "p_user_id": user_id,
                    "p_process_id": process_id,
                    "p_topic_name": topic_name,
                },
            )
            .execute()
            .data[0]
        )
        self.logger.info(f"Process {process_id} published to topic {topic_name}.")
        return TopicPublisher(
            id=response["_id"],
            user_id=user_id,
            process_id=process_id,
            topic_id=response["_topic_id"],
            topic_name=topic_name,
            topic_description=response["_topic_description"],
            message_format=response["_message_format"],
        )

    def create_topic_subscriber(
        self,
        user_id: str,
        process_id: str,
        topic_name: str,
    ) -> TopicSubscriber:
        self.logger.info(f"Creating topic subscription for process {process_id}")
        response = (
            self.client.rpc(
                "create_topic_subscriber",
                {
                    "p_user_id": user_id,
                    "p_process_id": process_id,
                    "p_topic_name": topic_name,
                },
            )
            .execute()
            .data[0]
        )
        self.logger.info(f"Process {process_id} subscribed to topic {topic_name}.")
        return TopicSubscriber(
            id=response["_id"],
            user_id=user_id,
            process_id=process_id,
            topic_id=response["_topic_id"],
            topic_name=topic_name,
            topic_description=response["_topic_description"],
            message_format=response["_message_format"],
        )

    def get_communication_protocols(self, process_id: str) -> CommunicationProtocols:
        return CommunicationProtocols(
            event_subscribers=self.get_event_subscribers(process_id),
            topic_publishers=self.get_topic_publishers(process_id),
            topic_subscribers=self.get_topic_subscribers(process_id),
            action_clients=self.get_action_clients(process_id),
            action_services=self.get_action_services(process_id),
            request_clients=self.get_request_clients(process_id),
            request_services=self.get_request_services(process_id),
        )

    def get_event_subscribers(self, process_id: str) -> Dict[str, EventSubscriber]:
        data = (
            self.client.table("event_subscribers")
            .select("*")
            .eq("process_id", process_id)
            .execute()
            .data
        )
        event_subscribers = []
        if not data:
            return event_subscribers
        for row in data:
            event_name = row["event_name"]
            event_subscribers[event_name] = EventSubscriber(
                id=row["id"],
                user_id=row["user_id"],
                process_id=process_id,
                event_type_id=row["event_type_id"],
                event_name=event_name,
                event_description=row["event_description"],
                event_format=row["event_format"],
            )
        return event_subscribers

    def get_action_clients(self, process_id: str) -> Dict[str, ActionClient]:
        data = (
            self.client.table("action_clients")
            .select("*")
            .eq("process_id", process_id)
            .execute()
            .data
        )
        action_clients = {}
        if not data:
            return action_clients
        for row in data:
            service_name = row["service_name"]
            action_clients[service_name] = ActionClient(
                id=row["id"],
                user_id=row["user_id"],
                process_id=process_id,
                process_name=row["name"],
                service_id=row["service_id"],
                service_name=service_name,
                service_description=row["service_description"],
                request_format=row["request_format"],
            )
        return action_clients

    def get_action_services(self, process_id: str) -> Dict[str, ActionService]:
        data = (
            self.client.table("action_services")
            .select("*")
            .eq("process_id", process_id)
            .execute()
            .data
        )
        action_services = {}
        if not data:
            return action_services
        for row in data:
            service_name = row["name"]
            action_services[service_name] = ActionService(
                id=row["id"],
                user_id=row["user_id"],
                process_id=process_id,
                data=ActionServiceData(
                    service_name=service_name,
                    service_description=row["description"],
                    request_format=row["request_format"],
                    feedback_format=row["feedback_format"],
                    response_format=row["response_format"],
                    tool_name=row["tool_name"],
                ),
            )
        return action_services

    def get_request_clients(self, process_id: str) -> Dict[str, RequestClient]:
        data = (
            self.client.table("request_clients")
            .select("*")
            .eq("process_id", process_id)
            .execute()
            .data
        )
        request_clients = {}
        if not data:
            return request_clients
        for row in data:
            service_name = row["service_name"]
            request_clients[service_name] = RequestClient(
                id=row["id"],
                user_id=row["user_id"],
                process_id=process_id,
                process_name=row["name"],
                service_id=row["service_id"],
                service_name=service_name,
                service_description=row["service_description"],
                request_format=row["request_format"],
            )
        return request_clients

    def get_request_services(self, process_id: str) -> Dict[str, RequestService]:
        data = (
            self.client.table("request_services")
            .select("*")
            .eq("process_id", process_id)
            .execute()
            .data
        )
        request_services = {}
        if not data:
            return request_services
        for row in data:
            service_name = row["name"]
            request_services[service_name] = RequestService(
                id=row["id"],
                user_id=row["user_id"],
                process_id=process_id,
                data=RequestServiceData(
                    service_name=service_name,
                    service_description=row["description"],
                    request_format=row["request_format"],
                    feedback_format=row["feedback_format"],
                    response_format=row["response_format"],
                    tool_name=row["tool_name"],
                ),
            )
        return request_services

    def get_topic_publishers(self, process_id: str) -> Dict[str, TopicPublisher]:
        data = (
            self.client.table("topic_publishers")
            .select("*")
            .eq("process_id", process_id)
            .execute()
            .data
        )
        topic_publishers = {}
        if not data:
            return topic_publishers
        for row in data:
            topic_name = row["topic_name"]
            topic_publishers[topic_name] = TopicPublisher(
                id=row["id"],
                user_id=row["user_id"],
                process_id=process_id,
                topic_id=row["topic_id"],
                topic_name=topic_name,
                topic_description=row["topic_description"],
                message_format=row["message_format"],
            )
        return topic_publishers

    def get_topic_subscribers(self, process_id: str) -> Dict[str, TopicSubscriber]:
        data = (
            self.client.table("topic_subscribers")
            .select("*")
            .eq("process_id", process_id)
            .execute()
            .data
        )
        topic_subscribers = {}
        if not data:
            return topic_subscribers
        for row in data:
            topic_name = row["topic_name"]
            topic_subscribers[topic_name] = TopicSubscriber(
                id=row["id"],
                user_id=row["user_id"],
                process_id=process_id,
                topic_id=row["topic_id"],
                topic_name=topic_name,
                topic_description=row["topic_description"],
                message_format=row["message_format"],
            )
        return topic_subscribers
