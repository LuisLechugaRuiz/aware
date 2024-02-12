import uuid
import zmq
import threading
from typing import Callable, Dict

from aware.utils.communication_protocols.actions.goal_handle import (
    GoalHandle,
    GoalHandleStatus,
)
from aware.utils.communication_protocols.actions.action import Action


class ActionClient:
    def __init__(
        self, broker_address: str, topic: str, callback: Callable, action_class: Action
    ):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.connect(broker_address)
        self.topic = topic

        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        self.active_goals: Dict[str, GoalHandle] = {}
        self.action_class = action_class
        self.callback = callback

        # Start feedback thread
        thread = threading.Thread(target=self.listen_for_feedback)
        thread.start()

    def send_goal(self, action):
        goal_id = str(uuid.uuid4())
        goal_handle = GoalHandle(goal_id, action)
        self.active_goals[goal_id] = goal_handle

        # Format the message with topic and send the goal
        message = f"{self.topic} {goal_handle.to_json()}"
        self.socket.send_string(message)

        return goal_handle

    def listen_for_feedback(self):
        while True:
            socks = dict(self.poller.poll(timeout=1000))  # Timeout in milliseconds
            if socks.get(self.socket) == zmq.POLLIN:
                multipart_response = self.socket.recv_multipart()
                message = multipart_response[-1].decode("utf-8")
                update = GoalHandle.from_json(message, self.action_class)
                if update.goal_id in self.active_goals:
                    self.callback(update.action)
                    if update.status in [
                        GoalHandleStatus.COMPLETED,
                        GoalHandleStatus.ABORTED,
                    ]:
                        del self.active_goals[update.goal_id]

    def update_goal(self, goal_handler: GoalHandle):
        if goal_handler.goal_id not in self.active_goals:
            raise ValueError("Goal ID does not exist")

        # Format the update message with topic
        update_message = f"{self.topic} update {GoalHandle.to_json(goal_handler)}"

        # Send the update message
        self.socket.send_string(update_message)

    def close(self):
        # Close sockets and context
        self.socket.close()
        self.context.term()

    def __del__(self):
        self.close()
