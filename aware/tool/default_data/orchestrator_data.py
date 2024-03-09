from dataclasses import dataclass

from aware.tool.default_data.data import Data

DEF_TASK = """Delegate atomic requests to the appropriate agents and manage the communication between them."""
# TODO: Add instructions


@dataclass
class Orchestrator(Data):
    @classmethod
    def get_tool_class(cls) -> str:
        return "Orchestrator"

    @classmethod
    def get_task(cls) -> str:
        return DEF_TASK
