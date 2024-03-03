from redis import Redis
from typing import List, Optional

from aware.process.process_data import ProcessData
from aware.process.process_ids import ProcessIds
from aware.process.state_machine.state import ProcessState


class ProcessRedisHandler:
    def __init__(self, client: Redis):
        self.client = client

    def create_process_state(self, process_id: str, process_state: ProcessState):
        self.client.sadd(
            f"process:{process_id}:states",
            process_state.to_json(),
        )

    def get_current_process_state(self, process_id: str) -> Optional[ProcessState]:
        data = self.client.get(f"process:{process_id}:current_state")
        if data:
            return ProcessState.from_json(data)
        return None

    def get_process_data(self, process_id: str) -> Optional[ProcessData]:
        data = self.client.get(f"process_data:{process_id}")
        if data:
            return ProcessData.from_json(data)
        return None

    def get_process_ids(self, process_id: str) -> Optional[ProcessIds]:
        data = self.client.get(f"process_ids:{process_id}")
        if data:
            return ProcessIds.from_json(data)
        return None

    def get_process_states(self, process_id: str) -> List[ProcessState]:
        process_states = self.client.smembers(f"process:{process_id}:states")
        return [
            ProcessState.from_json(process_state) for process_state in process_states
        ]

    def set_current_process_state(self, process_id: str, process_state: ProcessState):
        self.client.set(
            f"process:{process_id}:current_state",
            process_state.to_json(),
        )

    def set_process_data(self, process_id: str, process_data: ProcessData):
        self.client.set(
            f"process_data:{process_id}",
            process_data.to_json(),
        )

    def set_process_ids(self, process_ids: ProcessIds):
        self.client.set(
            f"process_ids:{process_ids.process_id}",
            process_ids.to_json(),
        )
