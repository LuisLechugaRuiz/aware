import json
import logging
from typing import Dict, Tuple
from time import sleep
from queue import Queue

from aware.architecture.helpers.tmp_ips import (
    DEF_ASSISTANT_IP,
    DEF_PUB_PORT,
    DEF_SUB_PORT,
    DEF_CLIENT_PORT,
    DEF_SERVER_PORT,
    DEF_ACTION_CLIENT_PORT,
    DEF_ACTION_SERVER_PORT,
)
from aware.architecture.helpers.topics import (
    DEF_ASSISTANT_MESSAGE,
    DEF_USER_MESSAGE,
    DEF_SEARCH_DATABASE,
    DEF_STORE_DATABASE,
    DEF_REGISTRATION_SERVER,
)
from aware.architecture.helpers.request import Request, RequestStatus
from aware.architecture.user.user_message import UserMessage
from aware.chat.chat import Chat
from aware.tools.tools_manager import ToolsManager
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

LOG = logging.getLogger(__name__)


class Assistant:
    """Your classical chatbot! But it can send requests to the system"""

    def __init__(self, assistant_ip: str):
        self.assistant_ip = assistant_ip
        self.requests: Dict[str, Request] = {}  # TODO: Get them from database
        self.active_goal_handles: Dict[str, Tuple[str, GoalHandle]] = {}
        self.chat = Chat(
            module_name="user",
            system_prompt_kwargs={"requests": self.get_requests()},
        )

        self.users: Dict[str, str] = {}
        self.user_messages: Queue[UserMessage] = Queue()

        # Action client for each user system.
        self.system_action_clients: Dict[str, ActionClient] = {}
        # Client for each user database.
        self.database_clients: Dict[str, Client] = {}

        # Communications
        self.proxy = Proxy(
            ip=assistant_ip, xsub_port=DEF_SUB_PORT, xpub_port=DEF_PUB_PORT
        )
        self.broker = Broker(
            ip=assistant_ip, client_port=DEF_CLIENT_PORT, server_port=DEF_SERVER_PORT
        )
        self.action_broker = ActionBroker(
            ip=assistant_ip,
            client_port=DEF_ACTION_CLIENT_PORT,
            server_port=DEF_ACTION_SERVER_PORT,
        )

        self.assistant_message_publisher = Publisher(
            address=f"tcp://{assistant_ip}:{DEF_SUB_PORT}",
            topic=DEF_ASSISTANT_MESSAGE,
        )
        self.users_message_subscriber = Subscriber(
            address=f"tcp://{assistant_ip}:{DEF_PUB_PORT}",
            topic=DEF_USER_MESSAGE,
            callback=self.user_message_callback,
        )

        # Server to handle user registration
        self.registration_server = Server(
            address=f"tcp://{assistant_ip}:{DEF_SERVER_PORT}",
            topics=[DEF_REGISTRATION_SERVER],
            callback=self.handle_registration,
        )

        self.assistant_functions = [
            self.communicate_with_users,
            self.send_request,
            self.search_user_info,
            self.store_user_info,
            self.wait_for_user,
        ]
        self.tools_manager = ToolsManager()

    # When registering we need also to create a new client to database.
    def handle_registration(self, message):
        """Register user creating a new action client connected to user's system"""

        # TODO: RECEIVE HERE!! THE USER UUID!
        user_info = json.loads(message)
        self.system_action_clients[user_info["user_name"]] = ActionClient(
            broker_address=f"tcp://{self.assistant_ip}:{DEF_ACTION_CLIENT_PORT}",
            topic=f"{user_info['user_name']}_system_action_server",
            callback=self.update_request,
            action_class=Request,
        )
        self.database_clients[user_info["user_name"]] = Client(
            address=f"tcp://{self.assistant_ip}:{DEF_CLIENT_PORT}",
        )
        print(f"Registered user: {user_info['user_name']}")
        return "Registered Successfully"

    def get_requests(self):
        request_str = "\n".join([str(value) for value in self.requests.values()])
        # self.requests = {}  # Resetting requests TODO: Decide when to reset requests.
        return request_str

    def broadcast_message(self, message: str):
        self.assistant_message_publisher.publish(message)

    def user_message_callback(self, user_message: str):
        # Save user message in a queue.
        message = UserMessage.from_json(user_message)
        print(
            colored(f"User {message.user_name}: ", "red")
            + f"message: {message.message}"
        )
        self.user_messages.put(message)

        # Broadcast to all users
        self.broadcast_message(user_message)

    def update_system(self):
        self.chat.edit_system_message(
            system_prompt_kwargs={"requests": self.get_requests()}
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
        return "Request sent."

    # NOT USED FOR NOW TO HAVE A GROUP COMMUNICATION - FOR NOW JUST BROADCASTING
    # def send_message_to_user(self, user_name: str, message: str):
    #     self.users[user_name].send_message(message)

    def communicate_with_users(self, message: str):
        """
        Communicate with the users.

        Args:
            message (str): The message to be sent.

        Returns:
            str
        """
        print(f'{colored("Assistant:", "blue")} {message}')
        assistant_message = UserMessage(user_name="Aware", message=message)
        self.broadcast_message(assistant_message.to_json())
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
            data = self.database_clients[user_name].send(
                topic=f"{user_name}_{DEF_SEARCH_DATABASE}", message=query
            )
            return f"Search returned: {data}"
        except Exception as e:
            return f"Error searching: {e}"

    def store_user_info(self, user_name: str, info: str):
        """
        Store the info on user's semantic database.

        Args:
            user_name (str): The user name.
            info (str): The info to be stored.

        Returns:
            str
        """
        print(f"STORING INFO: {info}")
        data = self.database_clients[user_name].send(
            topic=f"{user_name}_{DEF_STORE_DATABASE}", message=info
        )
        # self.database.store_user_info(user_name, info)
        # print(f"Storing {user_name}'s info: {info}")
        if data == "OK":
            return "Info stored."
        return "Error storing info."

    def wait_for_user(self):
        """
        Wait for user's input, use this function to stop execution until a new message is received.

        Args:
            None
        """
        print("Waiting for user's input...")
        self.running = False
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
            self.communicate_with_users(
                f"Request: {request.request}\n\nrequires feedback: {feedback}"
            )

            # Wait for feedback
            self.wait_user_message()

            # Send feedback
            user_message = self.user_messages.get()
            self.chat.conversation.add_user_message(
                message=user_message.message, user_name=user_message.user_name
            )
            self.user_messages.task_done()
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
            self.requests.pop(request.get_id())
            self.active_goal_handles.pop(request.get_id())
            self.user_messages.put(user_message)
            print(colored(f"{user_name}_system: ", "green") + message)
        elif request.get_status() == RequestStatus.FAILURE:
            user_name, goal_handle = self.active_goal_handles[request.get_id()]
            message = f"Request with id: {request.get_id()} failed with feedback: {request.get_feedback()}"
            user_message = UserMessage(
                user_name=f"{user_name}_system",
                message=message,
            )
            self.requests.pop(request.get_id())
            self.active_goal_handles.pop(request.get_id())
            self.user_messages.put(user_message)
            print(colored(f"{user_name}_system: ", "red") + message)

        self.update_system()

    def run(self):
        while True:
            while self.user_messages.empty():
                sleep(0.1)

            while not self.user_messages.empty():
                # Add user message to the chat
                user_message = self.user_messages.get()
                self.chat.conversation.add_user_message(
                    message=user_message.message, user_name=user_message.user_name
                )
                self.user_messages.task_done()

            self.running = True
            while self.running:
                tools_call = self.chat.call(functions=self.assistant_functions)
                if tools_call is None or not tools_call:
                    self.running = False
                    print("Stopping assistant due to None call.")
                elif isinstance(tools_call, str):
                    self.communicate_with_users(tools_call)
                    self.running = False
                else:
                    self.tools_manager.execute_tools(
                        tools_call=tools_call,
                        functions=self.assistant_functions,
                        chat=self.chat,
                    )

    def wait_user_message(self):
        while self.user_messages == []:
            sleep(0.1)


def main():
    assistant = Assistant(assistant_ip=DEF_ASSISTANT_IP)
    assistant.run()


if __name__ == "__main__":
    main()
