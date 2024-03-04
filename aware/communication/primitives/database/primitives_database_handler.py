from typing import Any, Dict, List, Optional

from aware.communication.primitives.database.primitives_redis_handler import (
    PrimitivesRedisHandler,
)
from aware.communication.primitives.database.primitives_supabase_handler import (
    PrimitiveSupabaseHandler,
)
from aware.communication.primitives.event import Event, EventStatus
from aware.communication.primitives.request import Request, RequestStatus
from aware.communication.primitives.topic import Topic
from aware.database.client_handlers import ClientHandlers
from aware.database.helpers import DatabaseResult


class PrimitivesDatabaseHandler:
    def __init__(self):
        self.redis_handler = PrimitivesRedisHandler(
            client=ClientHandlers().get_redis_client()
        )
        self.supabase_handler = PrimitiveSupabaseHandler(
            client=ClientHandlers().get_supabase_client()
        )

    def create_event(
        self, publisher_id: str, event_message: Dict[str, Any]
    ) -> DatabaseResult[Event]:
        try:
            event = self.supabase_handler.create_event(
                publisher_id=publisher_id,
                event_message=event_message,
            )
            self.redis_handler.create_event(event=event)
            return DatabaseResult(data=event)
        except Exception as e:
            return DatabaseResult(error=f"Error creating request: {e}")

    def create_event_type(
        self,
        user_id: str,
        event_name: str,
        event_description: str,
        message_format: Dict[str, Any],
    ):
        event_type = self.supabase_handler.create_event_type(
            user_id=user_id,
            event_name=event_name,
            event_description=event_description,
            message_format=message_format,
        )
        self.redis_handler.create_event_type(
            event_type=event_type,
        )

    # TODO: Adapt as create_event, we should only need client_id, request_message, priority, and is_async
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
    ) -> DatabaseResult[Request]:
        try:
            request = self.supabase_handler.create_request(
                user_id=user_id,
                service_id=service_id,
                client_id=client_id,
                client_process_id=client_process_id,
                client_process_name=client_process_name,
                request_message=request_message,
                priority=priority,
                is_async=is_async,
            )
            self.redis_handler.create_request(
                request=request,
            )
            return DatabaseResult(data=request)
        except Exception as e:
            return DatabaseResult(error=f"Error creating request: {e}")

    def create_request_type(
        self,
        user_id: str,
        request_name: str,
        request_format: Dict[str, str],
        feedback_format: Dict[str, str],
        response_format: Dict[str, str],
    ):
        self.supabase_handler.create_request_type(
            user_id=user_id,
            request_name=request_name,
            request_format=request_format,
            feedback_format=feedback_format,
            response_format=response_format,
        )

    def create_topic(
        self,
        user_id: str,
        topic_name: str,
        topic_description: str,
        agent_id: Optional[str] = None,
        is_private: bool = False,
    ) -> DatabaseResult[Topic]:
        try:
            topic = self.supabase_handler.create_topic(
                user_id, topic_name, topic_description, agent_id, is_private
            )
            self.redis_handler.create_topic(topic)
            return DatabaseResult(data=topic)
        except Exception as e:
            return DatabaseResult(error=f"Error creating request: {e}")

    def get_client_requests(self, client_id: str) -> List[Request]:
        return self.redis_handler.get_client_requests(client_id)

    def get_service_requests(self, service_id: str) -> List[Request]:
        return self.redis_handler.get_service_requests(service_id)

    def get_topic(self, topic_id: str) -> Optional[Topic]:
        return self.redis_handler.get_topic(topic_id)

    def set_event_notified(self, event: Event):
        event.status = EventStatus.NOTIFIED

        self.redis_handler.delete_event(event)
        self.supabase_handler.update_event(event)

    def set_request_completed(
        self, request: Request, success: bool, response: Dict[str, Any]
    ):
        request.data.response = response
        if success:
            request.data.status = RequestStatus.SUCCESS
        else:
            request.data.status = RequestStatus.FAILURE

        self.redis_handler.delete_request(request.id)
        self.supabase_handler.set_request_completed(request)

    def update_request_feedback(self, request: Request, feedback: str):
        request.data.feedback = feedback

        self.redis_handler.update_request(request)
        self.supabase_handler.update_request_feedback(request)

    def update_request_status(self, request: Request, status: RequestStatus):
        request.data.status = status

        self.redis_handler.update_request(request)
        self.supabase_handler.update_request_status(request)
