import asyncio
from typing import List

from aware.memory.user.user_working_memory import UserWorkingMemory
from aware.architecture.helpers.topics import (
    DEF_ASSISTANT_MESSAGE,
    DEF_USER_MESSAGE,
)
from aware.architecture.user.user_message import UserContextMessage, UserMessage
from aware.config.config import Config
from aware.utils.communication_protocols import Publisher, Subscriber
from aware.utils.communication_protocols.websocket.server import WebSocketServer
from aware.utils.logger.file_logger import FileLogger


class User:
    """User interface"""

    def __init__(
        self,
        assistant_ip: str,
    ):
        self.user_working_memory = UserWorkingMemory()
        self.user_name = self.user_working_memory.get_user_name()
        self.users_message_publisher = Publisher(
            address=f"tcp://{assistant_ip}:{Config().pub_port}", topic=DEF_USER_MESSAGE
        )
        self.assistant_message_subscriber = Subscriber(
            address=f"tcp://{assistant_ip}:{Config().sub_port}",
            topic=DEF_ASSISTANT_MESSAGE,
            callback=self.receive_assistant_message,
        )
        self.incoming_messages: List[UserMessage] = []
        self.logger = FileLogger("user", should_print=True)
        self.ws_server = WebSocketServer(
            host=Config().user_ip,
            port=Config().web_socket_port,
            callback=self.send_message,
        )

    def receive_assistant_message(self, message: str):
        user_message = UserMessage.from_json(message)
        self.user_working_memory.add_message(
            user_message
        )  # Only entry point to memory manager as assistant is the broker.
        if user_message.user_name != self.user_name:
            assistant_message = user_message.message
            self.logger.info(f"{Config().assistant_name}: {assistant_message}")
            self.incoming_messages.append(user_message)
            asyncio.run(self.ws_server.send_message(assistant_message))

    async def send_message(self, message: str):
        self.logger.info(f"{self.user_name}: {message}")
        user_message = UserMessage(user_name=self.user_name, message=message)
        user_context_message = UserContextMessage(
            user_message=user_message,
            context=self.user_working_memory.get_context(),
            thought=self.user_working_memory.get_thought(),
        )
        self.users_message_publisher.publish(user_context_message.to_json())
        self.incoming_messages.append(user_message)

    async def run(self):
        await self.ws_server.run()


async def main():
    user = User(
        assistant_ip=Config().assistant_ip,
    )
    await user.run()


if __name__ == "__main__":
    asyncio.run(main())
