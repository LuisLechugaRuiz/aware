from aware.agent.agent_state_machine import AgentState, AgentStateMachine
from aware.chat.conversation_schemas import JSONMessage
from aware.chat.conversation_buffer import ConversationBuffer
from aware.data.database.client_handlers import ClientHandlers
from aware.process.process_ids import ProcessIds
from aware.server.tasks import preprocess


class ProcessHandler:
    def __init__(self, process_ids: ProcessIds):
        self.process_ids = process_ids

    def add_message(
        self,
        message: JSONMessage,
    ):
        agent_data = ClientHandlers().get_agent_data(self.process_ids.agent_id)
        ClientHandlers().add_message(
            user_id=self.process_ids.user_id,
            process_id=self.process_ids.process_id,
            json_message=message,
        )
        if agent_data.state == AgentState.MAIN_PROCESS:
            # Add message to thought generator
            thought_generator_process_ids = self.get_process_ids(
                user_id=self.process_ids.user_id,
                agent_id=self.process_ids.agent_id,
                process_name="thought_generator_process_ids",
            )
            ClientHandlers().add_message(
                user_id=thought_generator_process_ids.user_id,
                process_id=thought_generator_process_ids.process_id,
                json_message=message,
            )
        elif agent_data.state == AgentState.THOUGHT_GENERATOR:
            # Add message to main process
            main_process_ids = self.get_process_ids(
                user_id=self.process_ids.user_id,
                agent_id=self.process_ids.agent_id,
                process_name="main",
            )
            ClientHandlers().add_message(
                user_id=main_process_ids.user_id,
                process_id=main_process_ids.process_id,
                json_message=message,
            )
        self._manage_conversation_buffer()

    def _manage_conversation_buffer(self):
        main_ids = self.get_process_ids(
            user_id=self.process_ids.user_id,
            agent_id=self.process_ids.agent_id,
            process_name="main",
        )

        assistant_conversation_buffer = ConversationBuffer(
            process_id=main_ids.process_id
        )

        ClientHandlers().publish(
            user_id=main_ids.user_id,
            topic_name="agent_interactions",
            topic_data=assistant_conversation_buffer.to_string(),
        )

        if assistant_conversation_buffer.should_trigger_warning():
            data_storage_manager_ids = self.get_process_ids(
                user_id=main_ids.user_id,
                agent_id=main_ids.agent_id,
                process_name="data_storage_manager",
            )
            preprocess.delay(data_storage_manager_ids.to_json())

            # CARE !!! Reset conversation buffer !!! - THIS CAN LEAD TO A RACE WITH THE TRIGGERS, WE NEED TO REMOVE AFTER THAT!!
            assistant_conversation_buffer.reset()

    def loop(self):
        preprocess.delay(self.process_ids.to_json())

    def on_transition(self):
        process = ClientHandlers().get_process(self.process_ids)
        next_state = AgentStateMachine().step(
            state=process.agent_data.state,
            process_communications=process.process_communications,
        )
        process.agent_data.state = next_state
        ClientHandlers().update_agent_data(process.agent_data)

        if next_state == AgentState.MAIN_PROCESS:
            main_process_ids = self.get_process_ids(
                user_id=self.process_ids.user_id,
                agent_id=self.process_ids.agent_id,
                process_name="main",
            )
            preprocess.delay(main_process_ids.to_json())
        elif next_state == AgentState.THOUGHT_GENERATOR:
            thought_generator_ids = self.get_process_ids(
                user_id=self.process_ids.user_id,
                agent_id=self.process_ids.agent_id,
                process_name="thought_generator",
            )
            preprocess.delay(thought_generator_ids.to_json())
        elif next_state == AgentState.IDLE:
            ClientHandlers().remove_active_process(self.process_ids)

    @classmethod
    def get_process_ids(self, user_id: str, agent_id: str, process_name: str):
        process_id = ClientHandlers().get_agent_process_id(
            agent_id=agent_id, process_name=process_name
        )
        return ProcessIds(
            user_id=user_id,
            agent_id=agent_id,
            process_id=process_id,
        )
