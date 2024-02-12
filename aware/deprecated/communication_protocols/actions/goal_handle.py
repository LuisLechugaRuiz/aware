import json
from enum import Enum
from aware.utils.communication_protocols.actions.action import Action


class GoalHandleStatus(Enum):
    ACTIVE = 1
    COMPLETED = 2
    ABORTED = 3


class GoalHandle:
    def __init__(self, goal_id, action: Action, status=GoalHandleStatus.ACTIVE):
        self.goal_id = goal_id
        self.action = action
        self.action_class = action.__class__
        self.status = status

    def to_json(self):
        return json.dumps(
            {
                "goal_id": self.goal_id,
                "action": self.action.to_json(),
                "status": self.status.name,
            }
        )

    @staticmethod
    def from_json(json_str, action_class: Action):
        data = json.loads(json_str)
        action = action_class.from_json(data["action"])
        return GoalHandle(data["goal_id"], action, GoalHandleStatus[data["status"]])

    def set_completed(self):
        self.status = GoalHandleStatus.COMPLETED

    def set_aborted(self):
        self.status = GoalHandleStatus.ABORTED
