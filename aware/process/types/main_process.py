from openai.types.chat import ChatCompletionMessageToolCall
from typing import Dict, List

from aware.communication.protocols.database.protocols_database_handler import (
    ProtocolsDatabaseHandler,
)
from aware.chat.conversation_schemas import ToolResponseMessage
from aware.process.process_interface import ProcessInterface
from aware.process.process_ids import ProcessIds


class MainProcess(ProcessInterface):
    """The main process class that should be used to handle the main process of the agent. This process is dependent on CommunicationProtocols."""

    def __init__(self, process_ids: ProcessIds):
        super().__init__(ids=process_ids)
        # TODO: Rename CommunicationProtocols to AgentCommunicationProtocols?
        self.communication_protocols = (
            ProtocolsDatabaseHandler().get_communication_protocols(
                process_id=process_ids.process_id
            )
        )

    def process_tool_calls(
        self, tool_calls: List[ChatCompletionMessageToolCall]
    ) -> bool:
        """Overrides process_tool_calls to consider communication protocols as tools."""
        should_continue = True
        for tool_call in tool_calls:
            # Check if it's a communication tool call
            communication_response = self.communication_protocols.process_tool_call(
                tool_call=tool_call
            )
            # TODO: Corner case: In case request is scheduled and there are other tool calls after that it will schedule request, call tools and then wait (don't step). Is this the expected behavior?
            if communication_response is not None:
                tool_response = ToolResponseMessage(
                    content=communication_response.result, tool_call_id=tool_call.id
                )
                self.process_handler.add_message(
                    process_ids=self.process_ids, message=tool_response
                )
                self.logger.info(
                    f"Triggered a communication tool call: {tool_call.function.name} with response: {communication_response.result}"
                )
                tool_continue = communication_response.should_continue
            else:
                tool_continue = self.execute_tool(tool_call=tool_call)
            if should_continue:
                should_continue = tool_continue
        return should_continue

    @property
    def prompt_kwargs(self) -> Dict[str, str]:
        """Overrides prompt_kwargs to consider communication protocols as tools."""
        return self.communication_protocols.to_prompt_kwargs()

    @property
    def tools_openai(self) -> List[ChatCompletionMessageToolCall]:
        """Overrides tools_openai to consider communication protocols as tools."""
        return self.communication_protocols.get_openai_tools()

    def step(self, should_continue: bool):
        """Step process on main only if should_continue is True. Otherwise it means that there is a synchronous request and we should not step the process.

        For main process we should always finish the process to
        """
        # TODO: Make this explicit without breaking new logic where communications are stored as Tools!
        if should_continue:
            self.logger.info("Stepping process.")
            self.process_handler.step(
                process_ids=self.process_ids,
                is_process_finished=True,
            )
        # TODO: Improve is_process_finished:
        #   We use this var as thought_generator should loop until generating the new thought, then we plan to add a decorator @stop_process, but this should not affect main...
        #   Now that we are splitting both processes it might make sense to rethink Agent StateMachine as we have explicit process.
