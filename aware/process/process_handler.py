from aware.agent.agent_state_machine import AgentState, AgentStateMachine
from aware.chat.conversation_schemas import (
    AssistantMessage,
    UserMessage,
    ToolResponseMessage,
    JSONMessage,
)
from aware.chat.conversation_buffer import ConversationBuffer
from aware.communication.primitives.request import Request, RequestStatus
from aware.data.database.client_handlers import ClientHandlers

from aware.agent.database.agent_database_handler import AgentDatabaseHandler
from aware.process.database.process_database_handler import ProcessDatabaseHandler
from aware.communication.protocols.database.protocols_database_handler import (
    ProtocolsDatabaseHandler,
)

from aware.process.process_ids import ProcessIds
from aware.process.process_data import ProcessFlowType
from aware.process.process_info import ProcessInfo
from aware.utils.logger.process_loger import ProcessLogger
from aware.server.celery_app import app


# TODO: REMOVE ALL DEPENDENCIES OF CLIENTHANDLERS.
class ProcessHandler:
    def __init__(self, process_logger: ProcessLogger):
        self.logger = process_logger.get_logger("process_handler")
        self.comm_protocols_database_handler = ProtocolsDatabaseHandler()
        self.agent_database_handler = AgentDatabaseHandler()
        self.process_database_handler = ProcessDatabaseHandler()

    # TODO: Refactor!
    def add_communications(self, process_ids: ProcessIds):
        # Get communications
        communication_protocols = (
            self.comm_protocols_database_handler.get_communication_protocols(
                process_id=process_ids.process_id
            )
        )
        event = communications.event
        if event is not None:
            self.add_message(
                process_ids=process_ids,
                message=UserMessage(name=event.message_name, content=event.content),
            )
            # Set event to notified and remove it from redis.
            # TODO: Add me!
            self.comm_protocols_database_handler.set_event_notified(event)

        request = communications.incoming_request
        if request is not None and request.data.status == RequestStatus.NOT_STARTED:
            self.add_message(
                process_ids=process_ids,
                message=UserMessage(
                    name=request.client_process_name,
                    content=request.query_to_string(),
                ),
            )
            # TODO: Add me!
            self.comm_protocols_database_handler.update_request_status(
                request, RequestStatus.IN_PROGRESS
            )

    def add_message(
        self,
        process_ids: ProcessIds,
        message: JSONMessage,
    ):
        agent_data = self.agent_database_handler.get_agent_data(process_ids.agent_id)
        # TODO: modify by chat database handler
        ClientHandlers().add_message(
            process_ids=process_ids,
            json_message=message,
        )
        if agent_data.state == AgentState.MAIN_PROCESS:
            # Add message to thought generator TODO: Address this properly to don't confuse the thought generator.
            thought_generator_process_ids = self.get_process_ids(
                user_id=process_ids.user_id,
                agent_id=process_ids.agent_id,
                process_name="thought_generator",
            )
            ClientHandlers().add_message(
                process_ids=thought_generator_process_ids,
                json_message=message,
            )
            self._manage_conversation_buffer(process_ids)

    # TODO: Thought should be an internal topic? - TODO: determine this as this will modify if we add it on conversation or as part of System message.
    def add_thought(
        self,
        process_ids: ProcessIds,
        thought: str,
    ):
        main_process_ids = self.get_process_ids(
            user_id=process_ids.user_id,
            agent_id=process_ids.agent_id,
            process_name="main",
        )
        message = AssistantMessage(name="thought", content=thought)
        ClientHandlers().add_message(process_ids=main_process_ids, json_message=message)
        self._manage_conversation_buffer(process_ids)

    def process_request(self, request: Request) -> Request:
        service_process_ids = self.process_database_handler.get_process_ids(
            process_id=request.service_process_id
        )
        self.start(service_process_ids)
        return f"Request {request.id} created successfully"

    def get_process_ids(self, user_id: str, agent_id: str, process_name: str):
        process_id = self.agent_database_handler.get_agent_process_id(
            agent_id=agent_id, process_name=process_name
        )
        return ProcessIds(
            user_id=user_id,
            agent_id=agent_id,
            process_id=process_id,
        )

    def _manage_conversation_buffer(self, process_ids: ProcessIds):
        main_ids = self.get_process_ids(
            user_id=process_ids.user_id,
            agent_id=process_ids.agent_id,
            process_name="main",
        )

        assistant_conversation_buffer = ConversationBuffer(
            process_id=main_ids.process_id
        )

        # TODO: modify by communication database handler and verify with internal topics...
        ClientHandlers().publish(
            user_id=main_ids.user_id,
            topic_name="agent_interactions",
            content=assistant_conversation_buffer.to_string(),
        )

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

    def preprocess(self, ids: ProcessIds):
        self.logger.info(f"Preprocessing process: {ids.process_id}")
        app.send_task("server.preprocess", kwargs={"process_ids_str": ids.to_json()})

    def start(self, process_ids: ProcessIds):
        if not self.agent_database_handler.is_agent_active(process_ids.agent_id):
            self.logger.info(f"Starting agent: {process_ids.agent_id}")
            self.step(process_ids=process_ids, is_process_finished=False)
        else:
            self.logger.info(f"Agent already active: {process_ids.agent_id}")

    def step(self, process_ids: ProcessIds, is_process_finished: bool = False):
        self.logger.info(f"On step: {process_ids.process_id}")
        process_info = self.process_database_handler.get_process_info(process_ids)
        if process_info.process_data.flow_type == ProcessFlowType.INTERACTIVE:
            self.step_state_machine(process_info, is_process_finished)
        elif process_info.process_data.flow_type == ProcessFlowType.INDEPENDENT:
            self.trigger_until_completion(process_ids, is_process_finished)

    def step_state_machine(self, process_info: ProcessInfo, is_process_finished: bool):
        agent_data = process_info.agent_data
        if agent_data.state == AgentState.IDLE:
            # Initialize process
            self.agent_database_handler.add_active_agent(
                agent_id=process_info.process_ids.agent_id
            )
            # Add communications
            self.add_communications(process_info.process_ids)

        agent_state_machine = AgentStateMachine(
            agent_data=agent_data,
            communications=process_info.communications,
            is_process_finished=is_process_finished,
        )
        next_state = agent_state_machine.step()
        agent_data.state = next_state
        self.agent_database_handler.update_agent_data(agent_data)
        self.logger.info(f"Next state: {next_state.value}")
        self.trigger_transition(process_info.process_ids, next_state)

    def trigger_transition(self, process_ids: ProcessIds, next_state: AgentState):
        if next_state == AgentState.MAIN_PROCESS:
            main_process_ids = self.get_process_ids(
                user_id=process_ids.user_id,
                agent_id=process_ids.agent_id,
                process_name="main",
            )
            self.preprocess(main_process_ids)
        elif next_state == AgentState.THOUGHT_GENERATOR:
            thought_generator_ids = self.get_process_ids(
                user_id=process_ids.user_id,
                agent_id=process_ids.agent_id,
                process_name="thought_generator",
            )
            self.preprocess(thought_generator_ids)
        elif next_state == AgentState.IDLE:
            self.agent_database_handler.remove_active_agent(process_ids.agent_id)

    def trigger_until_completion(
        self, process_ids: ProcessIds, is_process_finished: bool
    ):
        self.logger.info(f"Triggering until completion: {process_ids.process_id}")
        if is_process_finished:
            self.logger.info(f"Process {process_ids.process_id} finished.")
        else:
            self.preprocess(process_ids)
