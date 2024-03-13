from enum import Enum
from typing import List

from aware.process.database.process_database_handler import ProcessDatabaseHandler
from aware.process.state_machine.state import ProcessState
from aware.process.state_machine.transition import TransitionType
from aware.utils.logger.process_logger import ProcessLogger


class ProcessStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"


class ProcessStateMachine:
    def __init__(self, process_id: str, process_logger: ProcessLogger):
        self.logger = process_logger.get_logger("state_machine")
        self.process_id = process_id

        self.process_database_handler = ProcessDatabaseHandler()
        self.current_state = self.process_database_handler.get_current_process_state(process_id=process_id)
        self.states = self.process_database_handler.get_process_states(process_id=process_id)

        # TODO: get process status from database.
        self.status = ProcessStatus.RUNNING

        self.states_dict = {state.name: state for state in self.states}

    def get_current_state(self) -> ProcessState:
        return self.current_state

    def get_instructions(self) -> str:
        return self.current_state.instructions

    def get_status(self) -> ProcessStatus:
        return self.status

    def get_task(self) -> str:
        return self.current_state.task

    def get_tools(self) -> List[str]:
        self.current_state.tool_transitions.keys()

    def on_tool(self, tool_name: str):
        transition = self.current_state.tool_transitions.get(tool_name, None)
        if transition is None:
            raise ValueError(f"Tool {tool_name} didn't trigger a valid transition for state {self.current_state.name}")
        if transition.type == TransitionType.CONTINUE:
            return
        elif transition.type == TransitionType.END:
            self.current_state = self.states[0]  # Reset to initial state
            self.status = ProcessStatus.IDLE
        elif transition.type == TransitionType.OTHER:
            try:
                if transition.new_state is None:
                    raise ValueError("Transition is OTHER but new state is None, this is not allowed")
                self.current_state = self.states_dict[transition.new_state]
            except KeyError:
                raise ValueError(f"State {transition.new_state} does not exist")

    def update_current_state(self, state: ProcessState):
        self.current_state = state
        self.process_database_handler.update_current_process_state(process_id=self.process_id, process_state=state)
