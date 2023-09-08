import argparse
import logging
from typing import List

from aware.architecture.helpers.topics import (
    DEF_ASSISTANT_MESSAGE,
    DEF_USER_MESSAGE,
)
from aware.architecture.helpers.tmp_ips import (
    DEF_ASSISTANT_IP,
    DEF_PUB_PORT,
    DEF_SUB_PORT,
)
from aware.architecture.user.user_message import UserMessage
from aware.utils.communication_protocols import Publisher, Subscriber


LOG = logging.getLogger(__name__)


class User:
    """User interface"""

    def __init__(
        self,
        user_name: str,
        assistant_ip: str,
    ):
        # TODO: Fetch User database or start questionnaire if he is not in the database.
        self.user_name = user_name  # Temporal until we can gather info from database.

        # self.users_message_publisher = Publisher(
        #     address=f"tcp://{assistant_ip}:{assistant_port}", topic=DEF_USER_MESSAGE
        # )
        self.users_message_publisher = Publisher(
            address=f"tcp://{assistant_ip}:{DEF_SUB_PORT}", topic=DEF_USER_MESSAGE
        )
        self.assistant_message_subscriber = Subscriber(
            address=f"tcp://{assistant_ip}:{DEF_PUB_PORT}",
            topic=DEF_ASSISTANT_MESSAGE,
            callback=self.receive_assistant_message,
        )
        self.incoming_messages: List[UserMessage] = []

    def receive_assistant_message(self, message: str):
        self.incoming_messages.append(UserMessage.from_json(message))

    def send_message(self, message: str):
        user_message = UserMessage(user_name=self.user_name, message=message)
        self.users_message_publisher.publish(user_message.to_json())


# TODO: START USING THE RIGHT IP
def main():
    # TODO: Get user from local config and assistant from server config.
    parser = argparse.ArgumentParser(description="User configuration script.")
    parser.add_argument("-n", "--name", default="Luis", help="User name")

    args = parser.parse_args()

    user = User(
        args.name,
        assistant_ip=DEF_ASSISTANT_IP,
    )

    while True:
        user.run()


if __name__ == "__main__":
    main()
