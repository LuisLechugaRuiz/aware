from typing import Any, Dict, List, Optional

from aware.communication.helpers.current_input_metadata import CurrentInputMetadata
from aware.communication.primitives.database.primitives_redis_handler import (
    PrimitivesRedisHandler,
)
from aware.communication.primitives.database.primitives_supabase_handler import (
    PrimitiveSupabaseHandler,
)
from aware.communication.primitives.action import Action, ActionStatus
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

    def create_action(
        self, client_id: str, request_message: Dict[str, Any], priority: int
    ) -> DatabaseResult[Action]:
        try:
            action = self.supabase_handler.create_action(
                client_id=client_id,
                request_message=request_message,
                priority=priority,
            )
            self.redis_handler.create_action(
                action=action,
            )
            return DatabaseResult(data=action)
        except Exception as e:
            return DatabaseResult(error=f"Error creating action: {e}")

    def create_action_type(
        self,
        user_id: str,
        action_name: str,
        request_format: Dict[str, Any],
        feedback_format: Dict[str, Any],
        response_format: Dict[str, Any],
    ):
        self.supabase_handler.create_action_type(
            user_id=user_id,
            action_name=action_name,
            request_format=request_format,
            feedback_format=feedback_format,
            response_format=response_format,
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

    def create_request(
        self,
        client_id: str,
        request_message: Dict[str, Any],
        priority: int,
    ) -> DatabaseResult[Request]:
        try:
            request = self.supabase_handler.create_request(
                client_id=client_id,
                request_message=request_message,
                priority=priority,
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
        response_format: Dict[str, str],
    ):
        self.supabase_handler.create_request_type(
            user_id=user_id,
            request_name=request_name,
            request_format=request_format,
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

    def delete_current_input(self, process_id: str):
        self.redis_handler.delete_current_input_metadata(process_id)

    def get_current_input_metadata(
        self, process_id: str
    ) -> Optional[CurrentInputMetadata]:
        return self.redis_handler.get_current_input_metadata(process_id)

    def get_action(self, action_id: str) -> Optional[Action]:
        return self.redis_handler.get_action(action_id)

    def get_request(self, request_id: str) -> Optional[Request]:
        return self.redis_handler.get_request(request_id)

    def get_event(self, event_id: str) -> Optional[Event]:
        return self.redis_handler.get_event(event_id)

    def get_events(self, event_type_id: str) -> List[Event]:
        return self.redis_handler.get_events(event_type_id)

    def get_client_actions(self, client_id: str) -> List[Action]:
        return self.redis_handler.get_client_actions(client_id)

    def get_service_actions(self, service_id: str) -> List[Action]:
        return self.redis_handler.get_service_actions(service_id)

    def get_client_requests(self, client_id: str) -> List[Request]:
        return self.redis_handler.get_client_requests(client_id)

    def get_service_requests(self, service_id: str) -> List[Request]:
        return self.redis_handler.get_service_requests(service_id)

    def get_topic(self, topic_id: str) -> Optional[Topic]:
        return self.redis_handler.get_topic(topic_id)

    def send_action_feedback(self, action: Action, feedback: Dict[str, Any]):
        action.update_feedback(feedback)
        self.redis_handler.update_action(action, feedback)
        self.supabase_handler.update_action_feedback(action)

    def set_current_input_metadata(
        self, process_id: str, current_input_metadata: CurrentInputMetadata
    ):
        self.redis_handler.set_current_input_metadata(
            process_id, current_input_metadata
        )

    def set_event_notified(self, event: Event):
        event.status = EventStatus.NOTIFIED

        self.redis_handler.delete_event(event)
        self.supabase_handler.update_event(event)

    def set_action_completed(
        self, action: Action, response: Dict[str, Any], success: bool
    ):
        action.data.response = response
        if success:
            action.data.status = ActionStatus.SUCCESS
        else:
            action.data.status = ActionStatus.FAILURE

        self.redis_handler.delete_action(action)
        self.supabase_handler.set_action_completed(action)

    def set_request_completed(
        self, request: Request, response: Dict[str, Any], success: bool
    ):
        request.data.response = response
        if success:
            request.data.status = RequestStatus.SUCCESS
        else:
            request.data.status = RequestStatus.FAILURE

        self.redis_handler.delete_request(request.id)
        self.supabase_handler.set_request_completed(request)

    def update_action_status(self, action: Action, status: ActionStatus):
        action.data.status = status

        self.redis_handler.update_action(action)
        self.supabase_handler.update_action_status(action)

    def update_request_status(self, request: Request, status: RequestStatus):
        request.data.status = status

        self.redis_handler.update_request(request)
        self.supabase_handler.update_request_status(request)

    def update_topic(self, topic_id: str, message: Dict[str, Any]):
        self.redis_handler.update_topic(topic_id, message)
        self.supabase_handler.update_topic(topic_id, message)
