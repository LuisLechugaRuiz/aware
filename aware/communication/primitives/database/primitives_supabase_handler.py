from supabase import Client
from typing import Any, Dict, Optional

from aware.communication.primitives.event import Event, EventStatus, EventType
from aware.communication.primitives.request import (
    Request,
    RequestData,
    RequestStatus,
)
from aware.communication.primitives.topic import Topic
from aware.utils.logger.file_logger import FileLogger


class PrimitiveSupabaseHandler:
    def __init__(self, client: Client):
        self.client = client
        self.logger = FileLogger("supabase_handler")

    def create_event(self, publisher_id: str, event_message: Dict[str, Any]) -> Event:
        self.logger.info(
            f"Creating event using publisher: {publisher_id} with message: {event_message}"
        )
        response = (
            self.client.rpc(
                "create_event",
                {
                    "p_publisher_id": publisher_id,
                    "p_event_message": event_message,
                },
            )
            .execute()
            .data
        )
        response = response[0]
        return Event(
            id=response["id"],
            user_id=response["user_id"],
            event_type_id=response["event_type_id"],
            event_name=response["event_name"],
            event_description=response["event_description"],
            event_message=event_message,
            event_format=response["message_format"],
            status=EventStatus(response["status"]),
            timestamp=response["created_at"],
        )

    def create_event_type(
        self,
        user_id: str,
        event_name: str,
        event_description: str,
        message_format: Dict[str, Any],
    ) -> Event:
        self.logger.info(
            f"Creating event type {event_name} with description: {event_description} for user: {user_id}"
        )
        response = (
            self.client.table("event_types")
            .insert(
                {
                    "user_id": user_id,
                    "name": event_name,
                    "description": event_description,
                    "message_format": message_format,
                }
            )
            .execute()
            .data
        )
        response = response[0]
        return EventType(
            id=response["id"],
            user_id=user_id,
            name=event_name,
            description=event_description,
            message_format=message_format,
        )

    def create_request(
        self,
        user_id: str,
        service_id: str,
        client_id: str,
        client_process_id: str,
        client_process_name: str,
        request_message: Dict[str, Any],
        priority: int,
        is_async: bool,
    ) -> Request:
        self.logger.info(
            f"Creating request from client process: {client_process_name} to service: {service_id}"
        )
        response = (
            self.client.rpc(
                "create_request",
                {
                    "p_user_id": user_id,
                    "p_service_id": service_id,
                    "p_client_id": client_id,
                    "p_client_process_id": client_process_id,
                    "p_client_process_name": client_process_name,
                    "p_request_message": request_message,
                    "p_priority": priority,
                    "p_is_async": is_async,
                },
            )
            .execute()
            .data
        )
        request_data = RequestData(
            request=response["request"],
            feedback=response["feedback"],
            response=response["response"],
            priority=response["priority"],
            is_async=response["is_async"],
            status=RequestStatus(response["status"]),
        )
        return Request(
            request_id=response["id"],
            service_id=service_id,
            service_process_id=response["service_process_id"],
            client_id=client_id,
            client_process_id=client_process_id,
            client_process_name=client_process_name,
            timestamp=response["created_at"],
            data=request_data,
        )

    def create_request_type(
        self,
        user_id: str,
        request_name: str,
        request_format: Dict[str, str],
        feedback_format: Dict[str, str],
        response_format: Dict[str, str],
    ):
        self.logger.info(f"Creating request type {request_name}")
        response = (
            self.client.table("request_types")
            .insert(
                {
                    "user_id": user_id,
                    "name": request_name,
                    "request_format": request_format,
                    "feedback_format": feedback_format,
                    "response_format": response_format,
                }
            )
            .execute()
            .data
        )
        response = response[0]
        return response

    # TODO: call it properly to initialize topics.
    def create_topic(
        self,
        user_id: str,
        topic_name: str,
        topic_description: str,
        message_format: Dict[str, str],
        agent_id: Optional[str] = None,
        is_private: bool = False,
    ) -> Topic:
        existing_topic = (
            self.client.table("topics")
            .select("*")
            .eq("user_id", user_id)
            .eq("name", topic_name)
            .execute()
        ).data
        self.logger.info(f"Got existing topic: {existing_topic}")
        if not existing_topic:
            if agent_id is not None:
                new_topic_dict = {
                    "agent_id": agent_id,
                }
            else:
                new_topic_dict = {}

            self.logger.info(f"Creating topic {topic_name}")
            new_topic_dict.update(
                {
                    "user_id": user_id,
                    "name": topic_name,
                    "description": topic_description,
                    "message_format": message_format,
                    "is_private": is_private,
                }
            )

            existing_topic = (
                self.client.table("topics").insert(new_topic_dict).execute().data
            )
        existing_topic = existing_topic[0]
        return Topic(
            id=existing_topic["id"],
            user_id=user_id,
            name=topic_name,
            description=topic_description,
            message=existing_topic["message"],
            message_format=message_format,
            timestamp=existing_topic["updated_at"],
        )

    def set_request_completed(self, request: Request):
        self.client.table("requests").update(
            {"status": request.data.status.value, "response": request.data.response}
        ).eq("id", request.id).execute()

    def set_topic_content(self, user_id: str, name: str, content: str):
        data = (
            self.client.table("topics")
            .select("*")
            .eq("user_id", user_id)
            .eq("name", name)
            .execute()
            .data
        )
        if not data:
            raise Exception("Topic not found")
        else:
            self.client.table("topics").update({"content": content}).eq(
                "user_id", user_id
            ).eq("name", name).execute()

    def update_event(self, event: Event):
        self.client.table("events").update({"status": event.status.value}).eq(
            "id", event.id
        ).execute()

    def update_request_feedback(self, request: Request):
        self.client.table("requests").update({"feedback": request.data.feedback}).eq(
            "id", request.id
        ).execute()

    def update_request_status(self, request: Request):
        self.client.table("requests").update({"status": request.data.status.value}).eq(
            "id", request.id
        ).execute()
