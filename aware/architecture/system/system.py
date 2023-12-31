import argparse
from collections import OrderedDict
import json
from time import sleep

from aware.architecture.helpers import Request, RequestStatus
from aware.architecture.system.executor import Executor

# from aware.architecture.system.tool_creator import ToolCreator
from aware.utils.helpers import colored, get_local_ip
from aware.config.config import Config
from aware.architecture.helpers.topics import DEF_REGISTRATION_SERVER
from aware.utils.communication_protocols import Client
from aware.utils.communication_protocols.actions.action_server import (
    ActionServer,
    ServerGoalHandle,
)


# TODO: Join System | Planner | Executor into a single implementation.
class System:
    """Router for the system, completing the request from the user."""

    def __init__(
        self,
        user_name: str,
        assistant_ip: str,
    ):
        self.system_ip = get_local_ip()

        # self.tool_creator = ToolCreator()  # TODO: Next version.
        self.user_name = user_name
        self.requests: OrderedDict[str, Request] = OrderedDict()

        self.executor = Executor(
            get_user_feedback=self.get_user_feedback,
            user_name=user_name,
        )
        self.executor.register_tools()
        self.system_action_server = ActionServer(
            broker_address=f"tcp://{assistant_ip}:{Config().action_server_port}",
            topic=f"{user_name}_system_action_server",  # TODO: USE USER ID
            callback=self.execute_request,
            action_class=Request,
            update_callback=self.update_request_callback,
        )
        self.register_with_assistant(assistant_ip)

    def add_request(self, request: Request):
        # In case request already exists just update it.
        self.requests[request.get_id()] = request

    def execute_request(self, server_goal_handle: ServerGoalHandle):
        self.current_goal_handle = server_goal_handle
        request: Request = server_goal_handle.action
        print(colored("\n--- Request ---\n", "yellow"))
        print(request)
        self.update_request(
            request,
            status=RequestStatus.IN_PROGRESS,
            feedback="Starting to plan.",
        )
        execution = self.executor.execute(request=request)
        if execution.success:
            status = RequestStatus.SUCCESS
        else:
            status = RequestStatus.FAILURE
        # We need to notify to user OR create our own tool (On next version!!).
        self.update_request(request, status=status, feedback=execution.summary)

    # TODO: FIX ME! NOT WORKING PROPERLY THE RECEPTION.
    def get_user_feedback(self, request: Request):
        # Update request status
        request.update_status(status=RequestStatus.WAITING_USER_FEEDBACK)
        self.requests[request.get_id()] = request

        # Send feedback to user
        self.current_goal_handle.action = request
        self.current_goal_handle.send_feedback()

        # Wait for feedback
        while (
            self.requests[request.get_id()].get_status()
            == RequestStatus.WAITING_USER_FEEDBACK
        ):
            sleep(0.1)
        # Update request
        request = self.requests[request.get_id()]
        return request.get_feedback()

    def update_request(self, request: Request, status: RequestStatus, feedback: str):
        request.update_status(status=status, feedback=feedback)
        self.requests[request.get_id()] = request
        self.current_goal_handle.action = request

        if status == RequestStatus.SUCCESS:
            self.current_goal_handle.set_completed()
        elif status == RequestStatus.FAILURE:
            self.current_goal_handle.set_aborted()
        self.current_goal_handle.send_feedback()

    def update_request_callback(self, goal_handle: ServerGoalHandle):
        request = goal_handle.action
        self.requests[request.get_id()] = request
        self.current_goal_handle.action = request

    # TODO: receive ack.
    def register_with_assistant(
        self,
        assistant_ip: str,
    ):
        print("REGISTERING WITH ASSISTANT")
        client = Client(f"tcp://{assistant_ip}:{Config().client_port}")
        # TODO: Create class and add uuid.
        user_info = {
            "user_name": self.user_name,
        }
        client.send(
            topic=DEF_REGISTRATION_SERVER, message=json.dumps(user_info)
        )  # Send registration info to Assistant
        client.close()


def main():
    # TODO: Get USER FROM CONFIG!
    parser = argparse.ArgumentParser(description="User configuration script.")
    parser.add_argument("-n", "--name", default="Luis", help="User name")
    parser.add_argument(
        "-a",
        "--assistant_ip",
        type=str,
        default=Config().assistant_ip,
        help="Assistant IP",
    )
    args = parser.parse_args()

    # When user starts initialize his system.
    system = System(
        user_name=args.name,
        assistant_ip=args.assistant_ip,
    )
    while True:
        sleep(0.1)


if __name__ == "__main__":
    main()
