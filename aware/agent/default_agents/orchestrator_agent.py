DEF_TASK = """As orchestrator, an advanced virtual assistant capable of managing multiple agents to solve complex tasks,
your task is to delegate atomic requests to the appropriate agents and manage the communication between them."""


def get_orchestrator_task() -> str:
    return DEF_TASK


def get_orchestrator_tool_class() -> str:
    return "Assistant"
