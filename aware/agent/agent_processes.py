from dataclasses import dataclass


@dataclass
class AgentProcesses:
    main_process_id: str
    thought_generator_process_id: str
    context_manager_process_id: str
    data_storage_manager_process_id: str

    def to_dict(self):
        return {
            "main_process_id": self.main_process_id,
            "thought_generator_process_id": self.thought_generator_process_id,
            "context_manager_process_id": self.context_manager_process_id,
            "data_storage_manager_process_id": self.data_storage_manager_process_id,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)
