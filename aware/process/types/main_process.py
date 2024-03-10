from typing import Dict, List

from aware.communication.protocols.database.protocols_database_handler import (
    ProtocolsDatabaseHandler,
)
from aware.process.process_interface import ProcessInterface
from aware.process.process_ids import ProcessIds
from aware.tool.tool import Tool


class MainProcess(ProcessInterface):
    """The main process class that should be used to handle the main process of the agent. This process is dependent on CommunicationProtocols."""

    def __init__(self, process_ids: ProcessIds):
        super().__init__(ids=process_ids)
        self.agent_communication = ProtocolsDatabaseHandler().get_agent_communication(
            process_id=process_ids.process_id
        )

    @property
    def name(self) -> str:
        """Set the name of the main process to the agent name."""
        return self.agent_data.name

    @property
    def prompt_kwargs(self) -> Dict[str, str]:
        """Overrides prompt_kwargs to consider the data from agent communication"""
        return self.agent_communication.to_prompt_kwargs()

    @property
    def tools(self) -> List[Tool]:
        """Overrides tools to consider tools from agent communication."""
        return self.agent_communication.get_tools()

    @property
    def prompt_name(self) -> str:
        return "meta"

    def on_finish(self):
        self.agent_communication.set_input_completed()
