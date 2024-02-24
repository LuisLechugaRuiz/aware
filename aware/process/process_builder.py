from typing import Any, Dict, List, Optional

from aware.data.database.client_handlers import ClientHandlers
from aware.process.process_ids import ProcessIds
from aware.process.process_data import ProcessFlowType
from aware.process.state_machine.state import ProcessState


class ProcessBuilder:
    def __init__(
        self,
        user_id: str,
        agent_id: str,
    ):
        self.user_id = user_id
        self.agent_id = agent_id

    def create_process_by_config(
        self,
        process_config: Dict[str, Any],
        service_name: Optional[
            str
        ] = None,  # TODO: Remove when refactoring service - requests.
    ) -> ProcessIds:
        process_data = ClientHandlers().create_process(
            user_id=self.user_id,
            agent_id=self.agent_id,
            name=process_config["name"],
            tools_class=process_config["tools_class"],
            flow_type=ProcessFlowType(process_config["flow_type"]),
            service_name=service_name,
        )
        process_ids = ProcessIds(
            user_id=self.user_id,
            agent_id=self.agent_id,
            process_id=process_data.id,
        )
        return process_ids

    def create_process_communications(
        self, process_ids: ProcessIds, communications_config: Dict[str, Any]
    ) -> None:
        internal_events = communications_config["internal_events"]
        if len(internal_events) > 0:
            for event_name in internal_events:
                # TODO: Differentiate between internal and external events!!
                ClientHandlers().create_event_subscription(
                    process_ids=process_ids, event_name=event_name
                )
                # TODO: Include here topics - requests with external-internal differentiation.

                # TODO: Topics should be created first then subscriptions... we need publish - subscriber. Define along with request refactor - teams architecture to clarify comms.
                # ClientHandlers().create_topic(
                #     user_id=self.user_id,
                #     topic_name="agent_interactions",
                #     topic_description="Agent interactions:",
                # )
                # ClientHandlers().create_topic_subscription(
                #     process_id=data_storage_process_data.id,
                #     topic_name="agent_interactions",
                # )

    def create_process_state_machine(
        self, process_ids: ProcessIds, state_machine_config: Dict[str, Any]
    ) -> None:
        process_states: List[ProcessState] = []
        for state_name, state_info in state_machine_config.items():
            process_states.append(
                ClientHandlers().create_process_state(
                    user_id=self.user_id,
                    process_id=process_ids.process_id,
                    name=state_name,
                    task=state_info["task"],
                    instructions=state_info["instructions"],
                    tools=state_info["tools"],
                )
            )
        ClientHandlers().create_current_process_state(
            user_id=self.user_id,
            process_id=process_ids.process_id,
            process_state=process_states[
                0
            ],  # This forces the first state to be the initial state.
        )
