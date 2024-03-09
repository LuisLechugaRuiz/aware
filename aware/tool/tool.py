# Used to set a specific method as tool.
from abc import ABC
from typing import Any, Callable, Dict, Tuple


class Tool(ABC):
    def __init__(
        self,
        name: str,
        params: Dict[str, Tuple[Any, bool]],
        description: str,
        callback: Callable,
        should_continue: bool = True,
        run_remote: bool = False,
    ):
        self.name = name
        self.params = params
        self.description = description
        self.callback = callback
        self.should_continue = should_continue
        self.run_remote = run_remote
