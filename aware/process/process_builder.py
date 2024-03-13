from typing import Any, Dict, List

from aware.process.database.process_database_handler import ProcessDatabaseHandler
from aware.process.process_config import ProcessConfig
from aware.process.process_ids import ProcessIds
from aware.process.process_data import ProcessFlowType, ProcessType
from aware.process.state_machine.state import ProcessState


class ProcessBuilder:
    def __init__(
        self,
        user_id: str,
        agent_id: str,
    ):
        self.user_id = user_id
        self.agent_id = agent_id
        self.process_database_handler = ProcessDatabaseHandler()

    def create_process_by_config(
        self,
        process_config: ProcessConfig,
        process_type: ProcessType
    ) -> ProcessIds:
        process_data = self.process_database_handler.create_process(
            user_id=self.user_id,
            agent_id=self.agent_id,
            name=process_config.name,
            capability_class=process_config.capability_class,
            prompt_name=process_config.prompt_name,
            flow_type=ProcessFlowType(process_config.flow_type),
            process_type=process_type,
        )
        process_ids = ProcessIds(
            user_id=self.user_id,
            agent_id=self.agent_id,
            process_id=process_data.id,
        )
        return process_ids

    def create_process_state_machine(
        self, process_ids: ProcessIds, state_machine_states: List[ProcessState]
    ) -> None:
        process_states: List[ProcessState] = []
        for process_state in state_machine_states:
            process_states.append(
                self.process_database_handler.create_process_state(
                    user_id=self.user_id,
                    process_id=process_ids.process_id,
                    process_state=process_state,
                )
            )
        self.process_database_handler.create_current_process_state(
            user_id=self.user_id,
            process_id=process_ids.process_id,
            process_state=process_states[
                0
            ],  # This forces the first state to be the initial state.
        )
