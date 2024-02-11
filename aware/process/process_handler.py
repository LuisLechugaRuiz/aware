from aware.agent.agent_state_machine import AgentState, AgentStateMachine
from aware.chat.conversation_schemas import (
    AssistantMessage,
    UserMessage,
    ToolResponseMessage,
    JSONMessage,
)
from aware.chat.conversation_buffer import ConversationBuffer
from aware.communications.requests.request import Request
from aware.data.database.client_handlers import ClientHandlers
from aware.process.process_ids import ProcessIds
from aware.server.tasks import preprocess


class ProcessHandler:
    def __init__(self):
        self.supabase_handler = ClientHandlers().get_supabase_handler()
        self.redis_handler = ClientHandlers().get_redis_handler()

    def add_message(
        self,
        process_ids: ProcessIds,
        message: JSONMessage,
    ):
        agent_data = ClientHandlers().get_agent_data(process_ids.agent_id)
        ClientHandlers().add_message(
            user_id=process_ids.user_id,
            process_id=process_ids.process_id,
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
                user_id=thought_generator_process_ids.user_id,
                process_id=thought_generator_process_ids.process_id,
                json_message=message,
            )
            self._manage_conversation_buffer()

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
        self._manage_conversation_buffer()

    def create_event(
        self, user_id: str, event_name: str, message_name: str, content: str
    ):
        # - Add event to database
        event = ClientHandlers().create_event(
            user_id=user_id, event_name=event_name, content=content
        )
        # - Trigger the subscribed processes
        processes_id = ClientHandlers().get_processes_ids_by_event(
            user_id=user_id, event=event
        )
        for process_id in processes_id:
            user_message = UserMessage(name=message_name, content=content)
            ProcessHandler().add_message(process_ids=process_id, message=user_message)
            ProcessHandler().start(process_id)

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
            service_name=service_name,
            query=query,
            is_async=is_async,
        )
        # - Add the request as message and trigger the service process
        user_message = UserMessage(
            name=client_process_name, content=request.query_to_string()
        )
        ProcessHandler().add_message(
            process_ids=client_process_ids, message=user_message
        )
        ProcessHandler().start(process_id=request.service_process_id)
        return request

    def _manage_conversation_buffer(self, user_id: str, agent_id: str):
        main_ids = self.get_process_ids(
            user_id=user_id,
            agent_id=agent_id,
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
            preprocess.delay(data_storage_manager_ids.to_json())

            # CARE !!! Reset conversation buffer !!! - THIS CAN LEAD TO A RACE WITH THE TRIGGERS, WE NEED TO REMOVE AFTER THAT!!
            assistant_conversation_buffer.reset()

    def set_request_completed(self, request: Request, response: str):
        service_process = ClientHandlers().get_process(request.service_process_id)
        request.data.response = response
        request.data.status = "completed"

        redis_handler = ClientHandlers().get_redis_handler()
        client_process = ClientHandlers().get_process(request.client_process_id)

        # Add message to client process.
        if request.is_async():
            # - Async requests: Add new message with the response.
            ProcessHandler().add_message(
                process_ids=client_process.ids,
                json_message=UserMessage(
                    name=service_process.process_data.name, content=response
                ),
            )
        else:
            # - Sync requests: Update last conversation message with the response.
            client_conversation_with_keys = redis_handler.get_conversation_with_keys(
                request.client_process_id
            )
            message_key, message = client_conversation_with_keys[-1]
            if not isinstance(message, ToolResponseMessage):
                raise ValueError("Last message is not a tool response message.")
            message.content = request.data.response
            redis_handler.update_message(message_key, message)

        ProcessHandler().start(process_ids=client_process.ids)

        return ClientHandlers().set_request_completed(
            request=request,
        )

    def start(self, process_ids: ProcessIds):
        redis_handler = ClientHandlers().get_redis_handler()
        if not redis_handler.is_process_active(process_ids.process_id):
            redis_handler.add_active_process(process_ids.process_id)
            self.step(process_ids=process_ids, is_process_finished=False)

    def step(self, process_ids: ProcessIds, is_process_finished: bool = False):
        process = ClientHandlers().get_process(process_ids)
        agent_state_machine = AgentStateMachine(
            agent_data=process.agent_data,
            process_communications=process.process_communications,
            is_process_finished=is_process_finished,
        )
        next_state = agent_state_machine.step()
        process.agent_data.state = next_state
        ClientHandlers().update_agent_data(process.agent_data)

        if next_state == AgentState.MAIN_PROCESS:
            main_process_ids = self.get_process_ids(
                user_id=process_ids.user_id,
                agent_id=process_ids.agent_id,
                process_name="main",
            )
            preprocess.delay(main_process_ids.to_json())
        elif next_state == AgentState.THOUGHT_GENERATOR:
            thought_generator_ids = self.get_process_ids(
                user_id=process_ids.user_id,
                agent_id=process_ids.agent_id,
                process_name="thought_generator",
            )
            preprocess.delay(thought_generator_ids.to_json())
        elif next_state == AgentState.IDLE:
            ClientHandlers().remove_active_process(process_ids)

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
