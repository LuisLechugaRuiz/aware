from dataclasses import dataclass

from aware.tools.default_data.data import Data

DEF_IDENTITY = """You are orchestrator, an advanced virtual assistant capable of managing multiple agents to solve complex tasks"""
DEF_TASK = """Delegate atomic requests to the appropriate agents and manage the communication between them."""


@dataclass
class Orchestrator(Data):
    @classmethod
    def get_identity(cls) -> str:
        return DEF_IDENTITY

    @classmethod
    def get_task(cls) -> str:
        return DEF_TASK
