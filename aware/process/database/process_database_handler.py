from typing import Dict, List, Optional

from aware.agent.database.agent_database_handler import AgentDatabaseHandler
from aware.communication.protocols.database.protocols_database_handler import (
    ProtocolsDatabaseHandler,
)
from aware.process.database.process_redis_handler import (
    ProcessRedisHandler,
)
from aware.process.process_ids import ProcessIds
from aware.process.process_data import ProcessData, ProcessFlowType
from aware.process.process_info import ProcessInfo
from aware.process.state_machine.state import ProcessState
from aware.process.database.process_supabase_handler import (
    ProcessSupabaseHandler,
)
from aware.database.client_handlers import ClientHandlers
from aware.utils.logger.file_logger import FileLogger  # TODO: use agent logger?


class ProcessDatabaseHandler:
    def __init__(self):
        self.redis_handler = ProcessRedisHandler(
            client=ClientHandlers().get_redis_client()
        )
        self.supabase_handler = ProcessSupabaseHandler(
            client=ClientHandlers().get_supabase_client()
        )
        self.logger = FileLogger("process_agent_handler")
        self.agent_database_handler = AgentDatabaseHandler()
        self.comm_protocols_database_handler = ProtocolsDatabaseHandler()

    def create_current_process_state(
        self, user_id: str, process_id: str, process_state: ProcessState
    ):
        self.supabase_handler.create_current_process_state(
            user_id=user_id, process_id=process_id, process_state_id=process_state.id
        )
        self.redis_handler.set_current_process_state(process_id, process_state)
        return process_state

    # TODO: Two kind of instructions:
    # Task Instructions (To specify how to perform the task).
    # Tool Instructions: To specify how to use the tool. ( docstring )
    def create_process(
        self,
        user_id: str,
        agent_id: str,
        name: str,
        tools_class: str,
        flow_type: ProcessFlowType,
        service_name: Optional[str] = None,
    ) -> ProcessData:
        process_data = self.supabase_handler.create_process(
            user_id=user_id,
            agent_id=agent_id,
            name=name,
            tools_class=tools_class,
            flow_type=flow_type,
        )
        self.redis_handler.set_process_data(
            process_id=process_data.id, process_data=process_data
        )
        process_ids = ProcessIds(
            user_id=user_id, agent_id=agent_id, process_id=process_data.id
        )
        self.redis_handler.set_process_ids(process_ids)

        if service_name is None:
            service_name = name  # Use the name of the process, otherwise the name of the Agent. TODO: Solve this by internal and external requests.
        # TODO: Refactor based on new services - request system.
        # self.create_service(
        #     user_id=user_id,
        #     process_id=process_data.id,
        #     name=service_name,
        #     description=task,
        # )
        return process_data

    def create_process_state(
        self,
        user_id: str,
        process_id: str,
        name: str,
        task: str,
        instructions: str,
        tools: Dict[str, str],
    ):
        process_state = self.supabase_handler.create_process_state(
            user_id=user_id,
            process_id=process_id,
            name=name,
            task=task,
            instructions=instructions,
            tools=tools,
        )
        self.redis_handler.create_process_state(
            process_id=process_id, process_state=process_state
        )
        return process_state

    def get_current_process_state(self, process_id: str) -> ProcessState:
        current_process_state = self.redis_handler.get_current_process_state(process_id)

        if current_process_state is None:
            self.logger.info("Current process States not found in Redis")
            current_process_state = self.supabase_handler.get_current_process_state(
                process_id
            )
            if current_process_state is None:
                raise Exception("Current process States not found on Supabase")

            self.redis_handler.set_current_process_state(
                process_id, current_process_state
            )
        else:
            self.logger.info("Current process States found in Redis")
        return current_process_state

    def get_process_data(self, process_id: str) -> ProcessData:
        process_data = self.redis_handler.get_process_data(process_id)

        if process_data is None:
            self.logger.info("Process data not found in Redis")
            # Fetch agent data from Supabase
            process_data = self.supabase_handler.get_process_data(process_id)
            if process_data is None:
                raise Exception("Process data not found on Supabase")

            self.redis_handler.set_process_data(
                process_id=process_id, process_data=process_data
            )
        else:
            self.logger.info("Process data found in Redis")

        return process_data

    def get_process_ids(self, process_id: str) -> ProcessIds:
        process_ids = self.redis_handler.get_process_ids(process_id)

        if process_ids is None:
            self.logger.info("Process Ids not found in Redis")
            process_ids = self.supabase_handler.get_process_ids(process_id)
            if process_ids is None:
                raise Exception("Process Ids not found on Supabase")

            self.redis_handler.set_process_ids(process_ids)
        else:
            self.logger.info("Process Ids found in Redis")

        return process_ids

    def get_process_states(self, process_id: str) -> List[ProcessState]:
        process_states = self.redis_handler.get_process_states(process_id)

        if process_states is None:
            self.logger.info("Process States not found in Redis")
            process_states = self.supabase_handler.get_process_states(process_id)
            if process_states is None:
                raise Exception("Process States not found on Supabase")

            for process_state in process_states:
                self.redis_handler.create_process_state(process_id, process_state)
        else:
            self.logger.info("Process States found in Redis")
        return process_states

    def get_process_info(self, process_ids: ProcessIds) -> ProcessInfo:
        # Get agent data
        agent_data = self.agent_database_handler.get_agent_data(
            agent_id=process_ids.agent_id
        )
        # Get communications
        communication_protocols = (
            self.comm_protocols_database_handler.get_communication_protocols(
                process_id=process_ids.process_id
            )
        )
        # Get process data
        process_data = self.get_process_data(process_id=process_ids.process_id)
        process_states = self.get_process_states(process_id=process_ids.process_id)
        current_state = self.get_current_process_state(
            process_id=process_ids.process_id
        )

        return ProcessInfo(
            agent_data=agent_data,
            communication_protocols=communication_protocols,
            process_ids=process_ids,
            process_data=process_data,
            process_states=process_states,
            current_state=current_state,
        )

    def update_current_process_state(
        self, process_id: str, process_state: ProcessState
    ):
        self.redis_handler.set_current_process_state(
            process_id=process_id, process_state=process_state
        )
        self.supabase_handler.update_current_process_state(
            process_id=process_id, process_state_id=process_state.id
        )