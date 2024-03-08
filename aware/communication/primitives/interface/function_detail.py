from typing import Any, Callable, Dict


class FunctionDetail:
    def __init__(
        self,
        name: str,
        args: Dict[str, Any],
        description: str,
        callback: Callable,
        should_continue: bool,
    ):
        self.name = name
        self.args = args
        self.description = description
        self.callback = callback
        self.should_continue = should_continue
