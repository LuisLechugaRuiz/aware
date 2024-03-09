IS_DEFAULT_FUNCTION = "is_default_function"
IS_TOOL = "is_tool"
STOP_PROCESS = "stop_process"
RUN_REMOTE = "run_remote"


def stop_process(func):
    """Decorator to mark methods as process stoppers."""
    setattr(func, STOP_PROCESS, True)
    return func


def default_function(func):
    setattr(func, IS_DEFAULT_FUNCTION, True)
    return func


def tool(func):
    """Decorator to mark methods as tools."""
    setattr(func, IS_TOOL, True)
    return func


def run_remote(func):
    """Decorator to mark methods as remote tools."""
    setattr(func, RUN_REMOTE, True)
    return func