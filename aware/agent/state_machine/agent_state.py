from enum import Enum


# TODO: Split between agent state and the process that is running? TBD
class AgentState(Enum):
    IDLE = "idle"
    MAIN_PROCESS = "main_process"
    THOUGHT_GENERATOR = "thought_generator"
    FINISHED = "finished"
