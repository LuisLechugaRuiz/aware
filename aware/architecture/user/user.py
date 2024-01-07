import argparse
import logging
from typing import List

# TODO: USER NEW VERSION
from aware.agent.memory.user.user_memory_manager import UserMemoryManager
from aware.agent.memory.user_new.user_working_memory import UserWorkingMemory
from aware.architecture.helpers.topics import (
    DEF_ASSISTANT_MESSAGE,
    DEF_USER_MESSAGE,
)
from aware.architecture.user.user_message import UserContextMessage, UserMessage
from aware.config.config import Config
from aware.utils.communication_protocols import Publisher, Subscriber


LOG = logging.getLogger(__name__)


class User:
    """User interface"""

    def __init__(
        self,
        assistant_ip: str,
    ):
        self.user_memory_manager = UserWorkingMemory()
        self.user_name = self.user_memory_manager.get_name()
        self.users_message_publisher = Publisher(
            address=f"tcp://{assistant_ip}:{Config().pub_port}", topic=DEF_USER_MESSAGE
        )
        self.assistant_message_subscriber = Subscriber(
            address=f"tcp://{assistant_ip}:{Config().sub_port}",
            topic=DEF_ASSISTANT_MESSAGE,
            callback=self.receive_assistant_message,
        )
        self.incoming_messages: List[UserMessage] = []
        self.conversation_timer = None

    def receive_assistant_message(self, message: str):
        user_message = UserMessage.from_json(message)
        self.user_memory_manager.add_message(
            user_message
        )  # Only entry point to memory manager as assistant is the broker.
        self.incoming_messages.append(user_message)

    # TODO: SEND ALSO USER CONTEXT PROVIDED BY MEMORY MANAGER.
    def send_message(self, message: str):
        user_message = UserMessage(user_name=self.user_name, message=message)
        user_context_message = UserContextMessage(
            user_message=user_message,
            context=self.user_memory_manager.get_context(),
            thought=self.user_memory_manager.get_thought(),
        )
        self.users_message_publisher.publish(user_context_message.to_json())


# TODO: START USING THE RIGHT IP
def main():
    # TODO: Get user from local config and assistant from server config.
    parser = argparse.ArgumentParser(description="User configuration script.")
    parser.add_argument("-n", "--name", default="Luis", help="User name")

    args = parser.parse_args()

    user = User(
        args.name,
        assistant_ip=Config().assistant_ip,
    )

    while True:
        user.run()


if __name__ == "__main__":
    main()
