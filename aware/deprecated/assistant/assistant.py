import json
import logging
from typing import Dict, Tuple
from time import sleep
from queue import Queue

from aware.deprecated.old_agent import Agent
from aware.architecture.helpers.topics import (
    DEF_ASSISTANT_MESSAGE,
    DEF_USER_MESSAGE,
    DEF_GET_THOUGHT,
    DEF_REGISTRATION_SERVER,
)
from aware.architecture.helpers.request import Request, RequestStatus
from aware.architecture.user.user_message import UserMessage, UserContextMessage
from aware.deprecated.chat import Chat
from aware.config.config import Config

# from aware.tools.tools_manager import ToolsManager
from aware.utils.helpers import colored
from aware.utils.communication_protocols import (
    Proxy,
    Broker,
    Publisher,
    Subscriber,
    Client,
    Server,
    ActionClient,
    ActionBroker,
    GoalHandle,
)
from aware.utils.logger.file_logger import FileLogger

LOG = logging.getLogger(__name__)


class Assistant(Agent):
    """Your classical chatbot! But it can send requests to the system"""

    def __init__(self, assistant_ip: str):
        self.assistant_ip = assistant_ip
        self.requests: Dict[str, Request] = {}  # TODO: Get them from database
        self.active_goal_handles: Dict[str, Tuple[str, GoalHandle]] = {}
        self.context = ""
        self.thought = ""

        self.users: Dict[str, str] = {}
        self.user_context_messages: Queue[UserContextMessage] = Queue()

        # Action client for each user system.
        self.system_action_clients: Dict[str, ActionClient] = {}
        # Client for each user database.
        self.database_clients: Dict[str, Client] = {}

        # Communications
        self.proxy = Proxy(
            ip=assistant_ip, sub_port=Config().sub_port, pub_port=Config().pub_port
        )
        self.broker = Broker(
            ip=assistant_ip,
            client_port=Config().client_port,
            server_port=Config().server_port,
        )
        self.action_broker = ActionBroker(
            ip=assistant_ip,
            client_port=Config().action_client_port,
            server_port=Config().action_server_port,
        )

        self.assistant_message_publisher = Publisher(
            address=f"tcp://{assistant_ip}:{Config().pub_port}",
            topic=DEF_ASSISTANT_MESSAGE,
        )
        self.users_message_subscriber = Subscriber(
            address=f"tcp://{assistant_ip}:{Config().sub_port}",
            topic=DEF_USER_MESSAGE,
            callback=self.user_message_callback,
        )

        # Server to handle user registration
        self.registration_server = Server(
            address=f"tcp://{assistant_ip}:{Config().server_port}",
            topics=[DEF_REGISTRATION_SERVER],
            callback=self.handle_registration,
        )

        self.assistant_functions = [
            self.talk,
            self.send_request,
            self.search_user_info,
            # self.wait_for_user, TODO: Should we enable it to wait? Sometimes it can trigger this without answering..
        ]
        super().__init__(
            chat=Chat(
                module_name="assistant",
                logger=FileLogger("assistant"),
                system_prompt_kwargs={
                    "requests": self.get_requests(),
                    "context": self.context,
                    "thought": self.thought,
                },
            ),
            functions=self.assistant_functions,
            logger=FileLogger("assistant"),
        )

    # When registering we need also to create a new client to database.
    def handle_registration(self, message):
        """Register user creating a new action client connected to user's system"""

        # TODO: RECEIVE HERE!! THE USER UUID!
        user_info = json.loads(message)
        self.system_action_clients[user_info["user_name"]] = ActionClient(
            broker_address=f"tcp://{self.assistant_ip}:{Config().action_client_port}",
            topic=f"{user_info['user_name']}_system_action_server",
            callback=self.update_request,
            action_class=Request,
        )
        self.database_clients[user_info["user_name"]] = Client(
            address=f"tcp://{self.assistant_ip}:{Config().client_port}",
        )
        print(f"Registered user: {user_info['user_name']}")
        return "Registered Successfully"

    def get_requests(self):
        request_str = "\n".join([str(value) for value in self.requests.values()])
        # self.requests = {}  # Resetting requests TODO: Decide when to reset requests.
        return request_str

    def broadcast_message(self, message: str):
        self.assistant_message_publisher.publish(message)

    def user_message_callback(self, message_str: str):
        # Save user message in a queue.
        message = UserContextMessage.from_json(message_str)
        user_message = message.user_message
        print(
            colored(f"User {user_message.user_name}: ", "red")
            + f"message: {user_message.message}"
        )
        print(colored(f"CONTEXT: {message.context}", "green"))
        print(colored(f"THOUGHT: {message.thought}", "yellow"))
        self.user_context_messages.put(message)

        # Broadcast to all users
        self.broadcast_message(user_message.to_json())

    def update_system(self):
        "Overriding agent update system to also update the requests and the context"
        self.chat.edit_system_message(
            system_prompt_kwargs={
                "requests": self.get_requests(),
                "context": self.context,
                "thought": self.thought,
            }
        )

    def send_request(self, user_name: str, request: str):
        """
        Send a request to the system, make a very explicit request.

        Args:
            user_name (str): The name of the user which is running the system.
            request (str): The request the system needs to solve.

        Returns:
            None
        """

        new_request = Request(request=request)
        goal_handle = self.system_action_clients[user_name].send_goal(new_request)
        self.active_goal_handles[new_request.get_id()] = (user_name, goal_handle)
        self.update_request(new_request)
        print(colored(f"Request: {request}", "yellow"))
        return "Request sent to the system; the status will be updated soon."

    # NOT USED FOR NOW TO HAVE A GROUP COMMUNICATION - FOR NOW JUST BROADCASTING
    # def send_message_to_user(self, user_name: str, message: str):
    #     self.users[user_name].send_message(message)

    def talk(self, message: str):
        """
        Use this tool as the only way to communicate with the user.

        Args:
            message (str): The message to be sent.

        Returns:
            str
        """
        print(f'{colored("Assistant:", "blue")} {message}')
        assistant_message = UserMessage(
            user_name=Config().assistant_name, message=message
        )
        self.broadcast_message(assistant_message.to_json())
        self.stop_agent()
        return "Message sent."

    def search_user_info(self, user_name: str, query: str):
        """
        Search the query on user's semantic database.

        Args:
            user_name (str): The user name to be searched.
            query (str): The search query.

        Returns:
            str
        """
        try:
            print(f"Searching for {query} on {user_name}'s database")
            data = self.database_clients[user_name].send(
                topic=f"{user_name}_{DEF_GET_THOUGHT}", message=query
            )
            return f"Search returned: {data}"
        except Exception as e:
            return f"Error searching: {e}"

    def wait_for_user(self):
        """
        Wait for user's input, use this function to stop execution until a new message is received.

        Args:
            None
        """
        print("Waiting for user's input...")
        self.stop_agent()
        return "Waiting for user's input..."

    def update_request(self, request: Request):
        self.requests[request.get_id()] = request
        feedback = request.get_feedback()
        if request.get_status() == RequestStatus.WAITING_USER_FEEDBACK:
            # Ask for feedback
            print(
                f'{colored("Assistant request:", "red")} {request.request} requires feedback: {feedback}'
            )
            self.chat.conversation.add_assistant_message(
                f"Request: {request.request}\n\nRequires feedback: {feedback}"
            )
            self.talk(f"Request: {request.request}\n\nrequires feedback: {feedback}")

            # Wait for feedback
            self.wait_user_message()

            # Send feedback
            user_context_message = self.user_context_messages.get()
            user_message = user_context_message.user_message
            self.chat.conversation.add_user_message(
                message=user_message.message, user_name=user_message.user_name
            )
            self.user_context_messages.task_done()
            request.update_status(
                status=RequestStatus.IN_PROGRESS, feedback=user_message.message
            )

            # Update request
            user_name, goal_handle = self.active_goal_handles[request.get_id()]
            goal_handle.action = request
            self.system_action_clients[user_name].update_goal(goal_handle)
        elif request.get_status() == RequestStatus.SUCCESS:
            user_name, goal_handle = self.active_goal_handles[request.get_id()]
            message = f"Request with id: {request.get_id()} succeeded with feedback: {request.get_feedback()}"
            user_message = UserMessage(
                user_name=f"{user_name}_system",
                message=message,
            )
            user_context_message = UserContextMessage(
                user_message=user_message, context=self.context, thought=self.thought
            )
            self.requests.pop(request.get_id())
            self.active_goal_handles.pop(request.get_id())
            self.user_context_messages.put(user_context_message)
            print(colored(f"{user_name}_system: ", "green") + message)
        elif request.get_status() == RequestStatus.FAILURE:
            user_name, goal_handle = self.active_goal_handles[request.get_id()]
            message = f"Request with id: {request.get_id()} failed with feedback: {request.get_feedback()}"
            user_message = UserMessage(
                user_name=f"{user_name}_system",
                message=message,
            )
            user_context_message = UserContextMessage(
                user_message=user_message, context=self.context, thought=self.thought
            )
            # TODO: POP IT LATER!
            self.requests.pop(request.get_id())
            self.active_goal_handles.pop(request.get_id())
            self.user_context_messages.put(user_context_message)
            print(colored(f"{user_name}_system: ", "red") + message)

        self.update_system()

    def run(self):
        while True:
            while self.user_context_messages.empty():
                sleep(0.1)

            while not self.user_context_messages.empty():
                # Add user message to the chat
                user_context_message = self.user_context_messages.get()
                user_message = user_context_message.user_message
                self.context = user_context_message.context
                self.thought = user_context_message.thought
                self.chat.conversation.add_user_message(
                    message=user_message.message, user_name=user_message.user_name
                )
                self.update_system()
                self.user_context_messages.task_done()

            print("RUNNING AGENT!")
            message = self.run_agent()
            if message is not None:
                self.talk(message)

    def wait_user_message(self):
        while self.user_context_messages == []:
            sleep(0.1)


def main():
    assistant = Assistant(assistant_ip=Config().assistant_ip)
    assistant.run()


if __name__ == "__main__":
    main()
