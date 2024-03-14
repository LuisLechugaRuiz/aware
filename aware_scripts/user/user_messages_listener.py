from aware.communication.protocols.database.protocols_database_handler import ProtocolsDatabaseHandler
from aware.user.user_builder import UserBuilder
from aware.user.database.user_database_handler import UserDatabaseHandler
from aware.utils.logger.system_logger import SystemLogger
from aware.utils.logger.user_logger import UserLogger

from aware_scripts.communication.supabase_events_listener import SupabaseEventsListener


class Channel:
    def __init__(self, topic, event_type, callback):
        self.topic = topic
        self.event_type = event_type
        self.callback = callback


class UserMessagesListener(SupabaseEventsListener):
    def __init__(self):
        self.subscribe_to_channel(
            schema="public",
            table_name="user_messages",
            event_type="INSERT",
            callback=self.handle_message,
        )
        self.subscribe_to_channel(
            schema="public",
            table_name="user_requests",
            event_type="INSERT",
            callback=self.create_request,
        )
        self.subscribe_to_channel(
            schema="public",
            table_name="users_data",
            event_type="INSERT",
            callback=self.on_new_user,
        )
        self.logger = SystemLogger("user_messages")

    def handle_message(self, payload):
        try:
            message = payload["record"]
            user_id = message["user_id"]
            publisher_id = message["publisher_id"]
            event_message = message["event_message"]
            priority = message["priority"]

            user_logger = UserLogger(user_id).get_logger("user_messages")
            user_logger.info(f"Processing new user message: {event_message}")

            event_publisher = ProtocolsDatabaseHandler().get_event_publisher(publisher_id)
            event_publisher.create_event(
                event_message=event_message, priority=priority
            )
            UserDatabaseHandler().acknowledge_user_message(message["id"])
        except Exception as e:
            user_logger.error(f"Error handling new message: {e}")

    def create_request(self, payload):
        try:
            message = payload["record"]
            user_id = message["user_id"]
            client_id = message["client_id"]
            request_message = message["request_message"]
            priority = message["priority"]

            user_logger = UserLogger(user_id).get_logger("user_messages")
            user_logger.info(f"Processing new user request: {request_message}")

            request_client = ProtocolsDatabaseHandler().get_request_client(client_id)
            request_client.create_request(request_message, priority)
        except Exception as e:
            user_logger.error(f"Error handling new request: {e}")

    def on_new_user(self, payload):
        # Initialize user
        user_data = payload["record"]
        UserBuilder(user_data["user_id"]).initialize_user(
            user_name=user_data["name"], api_key=user_data["api_key"]
        )


def main():
    message_listener = UserMessagesListener()
    message_listener.start_realtime_listener()


if __name__ == "__main__":
    main()
