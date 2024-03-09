from typing import Any, Dict


class FunctionCall:
    def __init__(
        self,
        name: str,
        call_id: str,
        arguments: Dict[str, Any],
        run_remote: bool = False,
        should_continue: bool = True,
    ):
        self.name = name
        self.call_id = call_id
        self.arguments = arguments
        self.run_remote = run_remote
        self.should_continue = should_continue
