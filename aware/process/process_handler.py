from aware.agent.state_machine.agent_state_machine import AgentState, AgentStateMachine
from aware.agent.database.agent_database_handler import AgentDatabaseHandler
from aware.chat.conversation_schemas import (
    AssistantMessage,
    JSONMessage,
)
from aware.chat.conversation_buffer import ConversationBuffer
from aware.chat.database.chat_database_handler import ChatDatabaseHandler
from aware.communication.protocols.database.protocols_database_handler import (
    ProtocolsDatabaseHandler,
)
from aware.process.database.process_database_handler import ProcessDatabaseHandler
from aware.process.process_ids import ProcessIds
from aware.process.process_data import ProcessFlowType
from aware.process.process_info import ProcessInfo
from aware.utils.logger.process_logger import ProcessLogger
from aware.server.celery_app import app


class ProcessHandler:
    def __init__(self, process_ids: ProcessIds):
        self.process_database_handler = ProcessDatabaseHandler()
        process_info = self.process_database_handler.get_process_info(process_ids=process_ids)

        self.process_logger = ProcessLogger(
            user_id=self.process_ids.user_id, agent_name=process_info.agent_data.name, process_name=process_info.process_data.name
        )
        self.process_ids = process_ids

        self.comm_protocols_database_handler = ProtocolsDatabaseHandler()
        self.agent_database_handler = AgentDatabaseHandler(process_ids.user_id)
        self.chat_database_handler = ChatDatabaseHandler(self.process_logger)

    # TODO: refactor, lets rethink the logic.
    def add_message(self, message: JSONMessage):
        agent_data = self.agent_database_handler.get_agent_data(self.process_ids.agent_id)
        self.chat_database_handler.add_message(
            process_ids=self.process_ids,
            json_message=message,
        )
        if agent_data.state == AgentState.MAIN_PROCESS:
            # Add message to thought generator TODO: Address this properly to don't confuse the thought generator.
            thought_generator_process_ids = self.get_process_ids(
                user_id=self.process_ids.user_id,
                agent_id=self.process_ids.agent_id,
                process_name="thought_generator",
            )
            self.chat_database_handler.add_message(
                process_ids=thought_generator_process_ids,
                json_message=message,
            )
            self._manage_conversation_buffer()

    # TODO: Thought should be an internal topic? - TODO: determine this as this will modify if we add it on conversation or as part of System message.
    # TODO: I think it should be part of AgentData. Topics should be used for channels between agents which depends on use-cases, not for internal state.
    def add_thought(
        self,
        thought: str,
    ):
        # TODO: Refactor! Just save it at agent_data and show it at main prompt.
        main_process_ids = self.get_process_ids(
            user_id=self.process_ids.user_id,
            agent_id=self.process_ids.agent_id,
            process_name="main",
        )
        message = AssistantMessage(name="thought", content=thought)
        self.chat_database_handler.add_message(
            process_ids=main_process_ids, json_message=message
        )
        self._manage_conversation_buffer()

    def get_process_ids(self, user_id: str, agent_id: str, process_name: str):
        process_id = self.agent_database_handler.get_agent_process_id(
            agent_id=agent_id, process_name=process_name
        )
        return ProcessIds(
            user_id=user_id,
            agent_id=agent_id,
            process_id=process_id,
        )

    def _manage_conversation_buffer(self):
        main_ids = self.get_process_ids(
            user_id=self.process_ids.user_id,
            agent_id=self.process_ids.agent_id,
            process_name="main",
        )

        assistant_conversation_buffer = ConversationBuffer(
            process_id=main_ids.process_id, process_logger=self.process_logger
        )

        # TODO: modify by communication database handler and verify with internal topics...
        # TODO: we need to get publisher to publish agent_interactions. Determine if this should be a topic or directly AgentInfo.
        # agent_info.publish(
        #     user_id=main_ids.user_id,
        #     topic_name="agent_interactions",
        #     content=assistant_conversation_buffer.to_string(),
        # )

        if assistant_conversation_buffer.should_trigger_warning():
            self.logger.info(
                "Conversation buffer warning triggered, starting data storage manager."
            )
            data_storage_manager_ids = self.get_process_ids(
                user_id=main_ids.user_id,
                agent_id=main_ids.agent_id,
                process_name="data_storage_manager",
            )
            self.preprocess(data_storage_manager_ids)

            # CARE !!! Reset conversation buffer !!! - THIS CAN LEAD TO A RACE WITH THE TRIGGERS, WE NEED TO REMOVE AFTER THAT!! I think is okay as we are sharing the info with agent_interactions.
            assistant_conversation_buffer.reset()

    def preprocess(self):
        self.logger.info(f"Preprocessing process: {self.process_ids.process_id}")
        app.send_task("server.preprocess", kwargs={"process_ids_str": self.process_ids.to_json()})

    def start(self):
        if not self.agent_database_handler.is_agent_active(self.process_ids.agent_id):
            self.logger.info(f"Starting agent: {self.process_ids.agent_id}")
            self.step(is_process_finished=False)
        else:
            self.logger.info(f"Agent already active: {self.process_ids.agent_id}")

    def step(self, is_process_finished: bool):
        self.logger.info(f"On step: {self.process_ids.process_id}")
        process_info = self.process_database_handler.get_process_info(self.process_ids)
        # TODO: Step agent machine. - We need to consider agent state -> If agent is WAITING_FOR_RESPONSE then don't step it.
        #   One thing is the state machine (with specific transitions) and another is agent state (Idle, running, waiting_for_response).
        if process_info.process_data.flow_type == ProcessFlowType.INTERACTIVE:
            self.step_state_machine(process_info, is_process_finished)
        elif process_info.process_data.flow_type == ProcessFlowType.INDEPENDENT:
            self.trigger_until_completion(is_process_finished)

    def step_state_machine(self, process_info: ProcessInfo, is_process_finished: bool):
        agent_data = process_info.agent_data
        if agent_data.state == AgentState.IDLE:
            # Initialize process - TODO: refactor active_agents with AgentState.
            self.agent_database_handler.add_active_agent(
                agent_id=self.process_ids.agent_id
            )
            # Update input
            if self.comm_protocols_database_handler.has_current_input(self.process_ids.process_id):
                raise Exception(
                    "Trying to start process when input is already set, check the logic!!"
                )
            input_updated = self.update_input()
            if not input_updated:
                raise Exception(
                    "Trying to start process with no new input, check the logic!!"
                )

        agent_state_machine = AgentStateMachine(
            agent_data=agent_data,
            is_process_finished=is_process_finished,
        )
        next_state = agent_state_machine.step()

        # TODO: Clarify this function. It is used to update input or stop if input is completed and agent finished.
        if next_state == AgentState.FINISHED:
            agent_id = self.process_ids.agent_id
            self.logger.info(f"Agent: {agent_id} finished.")
            if not self.comm_protocols_database_handler.has_current_input():
                input_updated = self.update_input()
                if not input_updated:
                    self.logger.info(
                        f"No new input for agent: {agent_id}, setting state to IDLE."
                    )
                    agent_data.state = AgentState.IDLE
                else:
                    next_state = agent_state_machine.on_start()
            else:
                next_state = agent_state_machine.on_start()

        self.logger.info(f"Next state: {next_state.value}")
        agent_data.state = next_state
        self.agent_database_handler.update_agent_data(agent_data)
        self.trigger_transition(next_state)

    def trigger_transition(self, next_state: AgentState):
        if next_state == AgentState.MAIN_PROCESS:
            main_process_ids = self.get_process_ids(
                user_id=self.process_ids.user_id,
                agent_id=self.process_ids.agent_id,
                process_name="main",
            )
            self.preprocess(main_process_ids)
        elif next_state == AgentState.THOUGHT_GENERATOR:
            thought_generator_ids = self.get_process_ids(
                user_id=self.process_ids.user_id,
                agent_id=self.process_ids.agent_id,
                process_name="thought_generator",
            )
            self.preprocess(thought_generator_ids)
        elif next_state == AgentState.IDLE:
            self.agent_database_handler.remove_active_agent(self.process_ids.agent_id)

    def trigger_until_completion(
        self, is_process_finished: bool
    ):
        self.logger.info(f"Triggering until completion: {self.process_ids.process_id}")
        if is_process_finished:
            self.logger.info(f"Process {self.process_ids.process_id} finished.")
        else:
            self.preprocess(self.process_ids)

    def update_input(self) -> bool:
        process_id = self.process_ids.process_id
        input_updated = self.comm_protocols_database_handler.update_highest_prio_input(
            process_id=process_id
        )
        if input_updated:
            current_input, input_protocol = (
                self.comm_protocols_database_handler.get_current_input(
                    process_id=process_id
                )
            )
            new_input_message = current_input.input_to_user_message()
            self.add_message(self.process_ids, new_input_message)
            self.logger.info(
                f"Input updated for process: {process_id}, new input: {new_input_message.to_string()}"
            )
            # TODO: Should we update the current input status? prompt pending to processing...
            return True
        else:
            return False
