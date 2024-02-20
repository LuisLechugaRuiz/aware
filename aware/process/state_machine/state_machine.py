from enum import Enum
from typing import List

from aware.process.state_machine.state import ProcessState
from aware.utils.logger.file_logger import FileLogger


class Transitions(Enum):
    CONTINUE = "continue"
    END = "end"


class ProcessStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"


class ProcessStateMachine:
    def __init__(self, states: List[ProcessState], current_state: str):
        self.logger = FileLogger("state_machine")
        self.status = ProcessStatus.RUNNING

        self.states = states
        self.states_dict = {state.name: state for state in states}

        self.current_state = self.states_dict[current_state]

    def get_instructions(self) -> str:
        return self.current_state.instructions

    def get_status(self) -> ProcessStatus:
        return self.status

    def get_task(self) -> str:
        return self.current_state.task

    def get_tools(self) -> List[str]:
        self.current_state.tools.keys()

    def on_tool(self, tool_name: str):
        next_state = self.current_state.tools[tool_name]
        if next_state == Transitions.CONTINUE.value:
            return
        elif next_state == Transitions.END.value:
            self.current_state = self.states[0]  # Reset to initial state
            self.status = ProcessStatus.IDLE
        else:
            try:
                self.current_state = self.states_dict[next_state]
            except KeyError:
                raise ValueError(f"State {next_state} does not exist")
        return self.current_state
