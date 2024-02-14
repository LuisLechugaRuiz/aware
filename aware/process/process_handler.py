from aware.agent.agent_state_machine import AgentState, AgentStateMachine
from aware.chat.conversation_schemas import (
    AssistantMessage,
    UserMessage,
    ToolResponseMessage,
    JSONMessage,
)
from aware.chat.conversation_buffer import ConversationBuffer
from aware.communications.requests.request import Request, RequestStatus
from aware.data.database.client_handlers import ClientHandlers
from aware.process.process_ids import ProcessIds
from aware.utils.logger.file_logger import FileLogger
from aware.server.celery_app import app


def execute_task(task_name, *args, **kwargs):
    app.send_task(task_name, args=args, kwargs=kwargs)


# TODO: instead of adding the message DIRECTLY on event and request we should do it when initializing the process, in case of NEW request or NEW event we add them!!!
class ProcessHandler:
    def __init__(self):
        self.supabase_handler = ClientHandlers().get_supabase_handler()
        self.redis_handler = ClientHandlers().get_redis_handler()
        self.logger = FileLogger(name="process_handler")

    def add_communications(self, process_ids: ProcessIds):
        # Get communications
        process_communications = ClientHandlers().get_process_communications(
            process_id=process_ids.process_id
        )
        event = process_communications.event
        if event is not None:
            self.add_message(
                process_ids=process_ids,
                message=UserMessage(name=event.message_name, content=event.content),
            )
            # Set event to notified and remove it from redis.
            ClientHandlers().set_event_notified(event)

        request = process_communications.incoming_request
        if request is not None and request.data.status == RequestStatus.NOT_STARTED:
            self.add_message(
                process_ids=process_ids,
                message=UserMessage(
                    name=request.client_process_name,
                    content=request.query_to_string(),
                ),
            )
            ClientHandlers().update_request_status(request, RequestStatus.IN_PROGRESS)

    def add_message(
        self,
        process_ids: ProcessIds,
        message: JSONMessage,
    ):
        agent_data = ClientHandlers().get_agent_data(process_ids.agent_id)
        ClientHandlers().add_message(
            process_ids=process_ids,
            json_message=message,
        )
        if agent_data.state == AgentState.MAIN_PROCESS:
            # Add message to thought generator
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

    # TODO: Thought should be an internal event, add it when we split between internal and external (Events - Requests - Topics)
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

    def create_event(
        self, user_id: str, event_name: str, message_name: str, content: str
    ):
        self.logger.info(f"Creating event: {event_name} - {content}")
        # - Add event to database
        event = ClientHandlers().create_event(
            user_id=user_id,
            event_name=event_name,
            message_name=message_name,
            content=content,
        )
        self.logger.info("Event created on database")
        # - Trigger the subscribed processes
        processes_ids = ClientHandlers().get_processes_subscribed_to_event(
            user_id=user_id, event=event
        )
        self.logger.info(f"Processes subscribed to event: {processes_ids}")
        for process_ids in processes_ids:
            self.start(process_ids)

    def create_request(
        self,
        client_process_name: str,
        client_process_ids: ProcessIds,
        service_name: str,
        query: str,
        is_async: bool,
    ) -> Request:
        # - Save request in database
        request = ClientHandlers().create_request(
            process_ids=client_process_ids,
            client_process_name=client_process_name,
            service_name=service_name,
            query=query,
            is_async=is_async,
        )
        # - Start the service process if not running
        self.start(process_id=request.service_process_id)
        return request

    def get_process_ids(self, user_id: str, agent_id: str, process_name: str):
        process_id = ClientHandlers().get_agent_process_id(
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

        ClientHandlers().publish(
            user_id=main_ids.user_id,
            topic_name="agent_interactions",
            content=assistant_conversation_buffer.to_string(),
        )

        if assistant_conversation_buffer.should_trigger_warning():
            data_storage_manager_ids = self.get_process_ids(
                user_id=main_ids.user_id,
                agent_id=main_ids.agent_id,
                process_name="data_storage_manager",
            )
            self.preprocess(data_storage_manager_ids)

            # CARE !!! Reset conversation buffer !!! - THIS CAN LEAD TO A RACE WITH THE TRIGGERS, WE NEED TO REMOVE AFTER THAT!!
            assistant_conversation_buffer.reset()

    def preprocess(self, ids: ProcessIds):
        app.send_task("server.preprocess", kwargs={"process_ids_str": ids.to_json()})

    def set_request_completed(self, request: Request, response: str, success: bool):
        service_process_name = (
            ClientHandlers().get_process_data(request.service_process_id).name
        )

        redis_handler = ClientHandlers().get_redis_handler()
        client_process_ids = (
            ClientHandlers().get_process_info(request.client_process_id).process_ids
        )

        # Add message to client process.
        if request.is_async():
            # - Async requests: Add new message with the response and start the client process.
            self.add_message(
                process_ids=client_process_ids,
                json_message=UserMessage(name=service_process_name, content=response),
            )
            self.start(process_ids=client_process_ids)
        else:
            # - Sync requests: Update last conversation message with the response and step (continue from current state) the client process.
            client_conversation_with_keys = redis_handler.get_conversation_with_keys(
                request.client_process_id
            )
            message_key, message = client_conversation_with_keys[-1]
            if not isinstance(message, ToolResponseMessage):
                raise ValueError("Last message is not a tool response message.")
            message.content = request.data.response
            redis_handler.update_message(message_key, message)
            # TODO: Refine this logic, we should have more control over agents that are waiting for a response, split between the current transition and the state.
            self.step(process_ids=client_process_ids)

        return ClientHandlers().set_request_completed(
            request=request, success=success, response=response
        )

    def start(self, process_ids: ProcessIds):
        redis_handler = ClientHandlers().get_redis_handler()
        if not redis_handler.is_process_active(process_ids.process_id):
            self.logger.info(f"Starting process: {process_ids.process_id}")
            self.step(process_ids=process_ids, is_process_finished=False)
        else:
            self.logger.info(f"Process already active: {process_ids.process_id}")

    def step(self, process_ids: ProcessIds, is_process_finished: bool = False):
        self.logger.info(f"On step: {process_ids.process_id}")
        process_info = ClientHandlers().get_process_info(process_ids)
        agent_data = process_info.agent_data

        if agent_data.state == AgentState.IDLE:
            # Initialize process
            ClientHandlers().add_active_process(process_id=process_ids.process_id)
            # Add communications
            self.add_communications(process_ids)

        agent_state_machine = AgentStateMachine(
            agent_data=agent_data,
            process_communications=process_info.process_communications,
            is_process_finished=is_process_finished,
        )
        next_state = agent_state_machine.step()
        agent_data.state = next_state
        ClientHandlers().update_agent_data(agent_data)
        self.logger.info(f"Next state: {next_state.value}")
        self.trigger_transition(process_ids, next_state)

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
            ClientHandlers().remove_active_process(process_ids)
