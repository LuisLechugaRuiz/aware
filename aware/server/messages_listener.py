import asyncio
from realtime.connection import Socket
from typing import Callable, List
import threading
from typing import Optional


from aware.config.config import Config
from aware.data.database.client_handlers import ClientHandlers
from aware.process.process_handler import ProcessHandler
from aware.utils.logger.file_logger import FileLogger


class Channel:
    def __init__(self, topic, event_type, callback):
        self.topic = topic
        self.event_type = event_type
        self.callback = callback


class MessagesListener:
    def __init__(self):
        self.channels: List[Channel] = []
        self.realtime_url: str = (
            f"{Config().supabase_url}/realtime/v1/websocket?apikey={Config().supabase_key}&vsn=1.0.0".replace(
                "http", "ws"
            )
        )
        self.listen_task: Optional[threading.Thread] = None

    def on_user_message(self, payload):
        # Trigger Celery task
        logger = FileLogger(name="migration_tests")
        try:
            data = payload["record"]
            logger.info(f"Handling new message: {data}")

            user_id = data["user_id"]
            content = data["content"]
            user_data = ClientHandlers().get_user_data(user_id)
            logger.info(f"Processing new user message: {content}")
            ProcessHandler().create_event(
                user_id=user_id,
                event_name="user_message",
                message_name=user_data.user_name,
                content=content,
            )

            supabase_handler = ClientHandlers().get_supabase_handler()
            supabase_handler.remove_frontend_message(data["id"])
        except Exception as e:
            logger.error(f"Error handling new message: {e}")

    # TODO: do we need to run asyncio here? I think supabase-py is doing that now.
    def start_listen_task(self):
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        self.socket = Socket(url=self.realtime_url)
        self.socket.connect()
        for channel in self.channels:
            self.socket.set_channel(topic=channel.topic).join().on(
                channel.event_type, channel.callback
            )
        new_loop.run_until_complete(self.socket.listen())
        new_loop.close()

    def start_realtime_listener(self):
        if not self.listen_task:
            self.listen_task = threading.Thread(target=self.start_listen_task)
            self.listen_task.start()

    def subscribe_to_channel(
        self, schema: str, table_name: str, event_type: str, callback: Callable
    ):
        self.channels.append(
            Channel(
                topic=f"realtime:{schema}:{table_name}",
                event_type=event_type,
                callback=callback,
            )
        )


def main():
    message_listener = MessagesListener()
    message_listener.subscribe_to_channel(
        schema="public",
        table_name="frontend_messages",
        event_type="INSERT",
        callback=message_listener.on_user_message,
    )
    message_listener.start_realtime_listener()


if __name__ == "__main__":
    main()
