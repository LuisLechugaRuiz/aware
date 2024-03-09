from supabase import create_client
from redis import asyncio as aioredis
import redis
import threading
from typing import Any, Dict, List, Optional

from aware.agent.agent_data import AgentData
from aware.chat.conversation_schemas import (
    JSONMessage,
)
from aware.communication.communication_protocols import Communications
from aware.communication.events.event import Event, EventStatus
from aware.communication.events.event_type import EventType
from aware.communication.requests.request import Request, RequestStatus
from aware.communication.requests.request_service import RequestServiceData
from aware.config.config import Config
from aware.data.database.helpers import DatabaseResult
from aware.data.database.supabase_handler.supabase_handler import SupabaseHandler
from aware.data.database.redis_handler.redis_handler import RedisHandler
from aware.data.database.redis_handler.async_redis_handler import AsyncRedisHandler
from aware.process.process_ids import ProcessIds
from aware.process.process_data import ProcessData, ProcessFlowType
from aware.process.process_info import ProcessInfo
from aware.process.state_machine.state import ProcessState
from aware.memory.user.user_data import UserData
from aware.utils.logger.file_logger import FileLogger


class ClientHandlers:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ClientHandlers, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.supabase_client = create_client(
            Config().supabase_url, Config().supabase_key
        )
        self.supabase_handler = SupabaseHandler(self.supabase_client)
        self.redis_client = redis.Redis(host="localhost", port=6379, db=0)
        self.redis_handler = RedisHandler(self.redis_client)
        self.async_redis_client = aioredis.from_url(
            "redis://localhost", encoding="utf-8", decode_responses=True
        )
        # self.redis_client.flushall()
        # self.async_redis_client.flushall()
        self.async_redis_handler = AsyncRedisHandler(self.async_redis_client)
        self.logger = FileLogger("migration_client_handlers", should_print=True)

    def add_active_agent(self, agent_id: str):
        self.redis_handler.add_active_agent(agent_id)
        self.supabase_handler.set_active_agent(agent_id, active=True)

    def add_message(
        self,
        process_ids: ProcessIds,
        json_message: JSONMessage,
    ):
        redis_handlers = self.get_redis_handler()
        supabase_handlers = self.get_supabase_handler()
        self.logger.info("Adding to supa")
        chat_message = supabase_handlers.add_message(
            process_id=process_ids.process_id,
            user_id=process_ids.user_id,
            json_message=json_message,
        )
        self.logger.info("Adding to redis")
        redis_handlers.add_message(
            process_id=process_ids.process_id, chat_message=chat_message
        )
        return chat_message

    def create_agent(
        self,
        user_id: str,
        name: str,
        capability_class: str,
        memory_mode: str,
        modalities: List[str],
        thought_generator_mode: str,
    ) -> AgentData:
        self.logger.info("Creating agent")
        agent_data = self.supabase_handler.create_agent(
            user_id=user_id,
            name=name,
            capability_class=capability_class,
            memory_mode=memory_mode,
            modalities=modalities,
            thought_generator_mode=thought_generator_mode,
        )
        self.logger.info(f"Agent: {agent_data.id}, created on supabase")
        self.redis_handler.set_agent_data(agent_data)
        self.logger.info(f"Agent: {agent_data.id}, created on redis")
        return agent_data

    def create_current_process_state(
        self, user_id: str, process_id: str, process_state: ProcessState
    ):
        self.supabase_handler.create_current_process_state(
            user_id=user_id, process_id=process_id, process_state_id=process_state.id
        )
        self.redis_handler.set_current_process_state(process_id, process_state)
        return process_state

    # TODO: Two kind of instructions:
    # Task Instructions (To specify how to perform the task).
    # Tool Instructions: To specify how to use the tool. ( docstring )
    def create_process(
        self,
        user_id: str,
        agent_id: str,
        name: str,
        capability_class: str,
        flow_type: ProcessFlowType,
        service_name: Optional[str] = None,
    ) -> ProcessData:
        process_data = self.supabase_handler.create_process(
            user_id=user_id,
            agent_id=agent_id,
            name=name,
            capability_class=capability_class,
            flow_type=flow_type,
        )
        self.redis_handler.set_process_data(
            process_id=process_data.id, process_data=process_data
        )
        process_ids = ProcessIds(
            user_id=user_id, agent_id=agent_id, process_id=process_data.id
        )
        self.redis_handler.set_process_ids(process_ids)

        if service_name is None:
            service_name = name  # Use the name of the process, otherwise the name of the Agent. TODO: Solve this by internal and external requests.
        # TODO: Refactor based on new services - request system.
        # self.create_service(
        #     user_id=user_id,
        #     process_id=process_data.id,
        #     name=service_name,
        #     description=task,
        # )
        return process_data

    def create_process_state(
        self,
        user_id: str,
        process_id: str,
        name: str,
        task: str,
        instructions: str,
        tools: Dict[str, str],
    ):
        process_state = self.supabase_handler.create_process_state(
            user_id=user_id,
            process_id=process_id,
            name=name,
            task=task,
            instructions=instructions,
            tools=tools,
        )
        self.redis_handler.create_process_state(
            process_id=process_id, process_state=process_state
        )
        return process_state

    def create_event(self, publisher_id: str, event_message: Dict[str, Any]) -> Event:
        event = self.supabase_handler.create_event(
            publisher_id=publisher_id,
            event_message=event_message,
        )
        self.redis_handler.create_event(event=event)
        return event

    def create_event_subscriber(self, process_ids: ProcessIds, event_name: str):
        event_subscriber = self.supabase_handler.create_event_subscriber(
            user_id=process_ids.user_id,
            process_id=process_ids.process_id,
            event_name=event_name,
        )
        self.redis_handler.create_event_subscriber(
            process_ids=process_ids, event_subscriber=event_subscriber
        )
        self.logger.info(
            f"Created subscription of process_id: {process_ids.process_id} to event: {event_name}"
        )

    def create_event_type(
        self,
        user_id: str,
        event_name: str,
        event_description: str,
        message_format: Dict[str, Any],
    ) -> EventType:
        event_type = self.supabase_handler.create_event_type(
            user_id=user_id,
            event_name=event_name,
            event_description=event_description,
            message_format=message_format,
        )
        self.redis_handler.create_event_type(
            event_type=event_type,
        )
        return event_type

    def create_request(
        self,
        user_id: str,
        service_id: str,
        client_id: str,
        client_process_id: str,
        client_process_name: str,
        request_message: Dict[str, Any],
        priority: int,
        is_async: bool,
    ) -> DatabaseResult[Request]:
        try:
            request = self.supabase_handler.create_request(
                user_id=user_id,
                service_id=service_id,
                client_id=client_id,
                client_process_id=client_process_id,
                client_process_name=client_process_name,
                request_message=request_message,
                priority=priority,
                is_async=is_async,
            )
        except Exception as e:
            return DatabaseResult(error=f"Error creating request: {e}")
        self.redis_handler.create_request(
            request=request,
        )
        return DatabaseResult(data=request)

    def create_request_client(self, user_id: str, process_id: str, service_name: str):
        request_client = self.supabase_handler.create_request_client(
            user_id=user_id, process_id=process_id, service_name=service_name
        )
        self.redis_handler.create_request_client(request_client=request_client)

    def create_request_service(
        self,
        user_id: str,
        process_id: str,
        service_name: str,
        service_description: str,
        request_name: str,
        tool_name: Optional[str] = None,
    ):
        """Create new service"""
        request_service = self.supabase_handler.create_request_service(
            user_id=user_id,
            process_id=process_id,
            service_name=service_name,
            service_description=service_description,
            request_name=request_name,
            tool_name=tool_name,
        )
        self.redis_handler.create_request_service(request_service=request_service)

    def create_topic_subscriber(self, user_id: str, process_id: str, topic_name: str):
        topic_subscriber = self.supabase_handler.create_topic_subscriber(
            user_id=user_id,
            process_id=process_id,
            topic_name=topic_name,
        )
        self.redis_handler.create_topic_subscriber(topic_subscriber)
        self.logger.info(
            f"Created subscriber for process_id: {process_id} to topic: {topic_name}"
        )

    def create_topic_publisher(self, user_id: str, process_id: str, topic_name: str):
        topic_publisher = self.supabase_handler.create_topic_publisher(
            user_id=user_id,
            process_id=process_id,
            topic_name=topic_name,
        )
        self.redis_handler.create_topic_publisher(topic_publisher)
        self.logger.info(
            f"Created publisher for process_id: {process_id} to topic: {topic_name}"
        )

    def create_topic(
        self,
        user_id: str,
        topic_name: str,
        topic_description: str,
        agent_id: Optional[str] = None,
        is_private: bool = False,
    ):
        topic = self.supabase_handler.create_topic(
            user_id, topic_name, topic_description, agent_id, is_private
        )
        self.redis_handler.create_topic(topic)
        self.logger.info(f"Created topic: {topic_name}")

    def create_capability(self, process_ids: ProcessIds, capability_name: str):
        # TODO: Check if capability exists first on redis and supabase
        capability = self.supabase_handler.create_capability(
            process_ids, capability_name
        )
        self.redis_handler.create_capability(process_ids, capability)
        self.logger.info(
            f"Created capability for process_id: {process_ids.process_id} with name: {capability_name}"
        )

    def create_capability_variable(
        self, capability_id: str, variable_name: str, variable_content: str
    ):
        self.supabase_handler.create_capability_variable(
            capability_id, variable_name, variable_content
        )
        self.redis_handler.create_capability_variable(
            capability_id, variable_name, variable_content
        )

    # TODO: fetch from supabase as fallback
    def get_agent_id_by_process_id(self, process_id: str) -> str:
        return self.redis_handler.get_agent_id_by_process_id(process_id)

    def get_supabase_handler(self):
        return self._instance.supabase_handler

    def get_async_redis_handler(self) -> AsyncRedisHandler:
        return self._instance.async_redis_handler

    def get_redis_handler(self) -> RedisHandler:
        return self._instance.redis_handler

    def get_agent_data(self, agent_id: str) -> AgentData:
        agent_data = self.redis_handler.get_agent_data(agent_id)

        if agent_data is None:
            self.logger.info("Agent data not found in Redis")
            # Fetch agent data from Supabase
            agent_data = self.supabase_handler.get_agent_data(agent_id)
            if agent_data is None:
                raise Exception("Agent data not found")

            self.redis_handler.set_agent_data(agent_data)
        else:
            self.logger.info("Agent data found in Redis")

        return agent_data

    def get_agent_process_id(self, agent_id: str, process_name: str) -> str:
        process_id = self.redis_handler.get_agent_process_id(agent_id, process_name)

        if process_id is None:
            self.logger.info("Agent process id not found in Redis")
            # Fetch agent process id from Supabase
            process_id = self.supabase_handler.get_agent_process_id(
                agent_id, process_name
            )
            if process_id is None:
                raise Exception("Agent process id not found")

            self.redis_handler.set_agent_process_id(agent_id, process_name, process_id)
        else:
            self.logger.info("Agent process id found in Redis")

        return process_id

    def get_current_process_state(self, process_id: str) -> ProcessState:
        current_process_state = self.redis_handler.get_current_process_state(process_id)

        if current_process_state is None:
            self.logger.info("Current process States not found in Redis")
            current_process_state = self.supabase_handler.get_current_process_state(
                process_id
            )
            if current_process_state is None:
                raise Exception("Current process States not found on Supabase")

            self.redis_handler.set_current_process_state(
                process_id, current_process_state
            )
        else:
            self.logger.info("Current process States found in Redis")
        return current_process_state

    def get_process_data(self, process_id: str) -> ProcessData:
        process_data = self.redis_handler.get_process_data(process_id)

        if process_data is None:
            self.logger.info("Process data not found in Redis")
            # Fetch agent data from Supabase
            process_data = self.supabase_handler.get_process_data(process_id)
            if process_data is None:
                raise Exception("Process data not found on Supabase")

            self.redis_handler.set_process_data(
                process_id=process_id, process_data=process_data
            )
        else:
            self.logger.info("Process data found in Redis")

        return process_data

    def get_communication_protocols(self, process_id: str) -> CommunicationProtocols:
        communications = self.redis_handler.get_communications(
            process_id=process_id,
        )

        if communications is None:
            self.logger.info("Process Communications not found in Redis")
            communications = self.supabase_handler.get_communications(
                process_id=process_id
            )
            if communications is None:
                raise Exception("Process Communications not found on Supabase")

            self.redis_handler.set_communications(
                process_id=process_id, communications=communications
            )
        else:
            self.logger.info("Process Communications found in Redis")

        return communications

    def get_process_ids(self, process_id: str) -> ProcessIds:
        process_ids = self.redis_handler.get_process_ids(process_id)

        if process_ids is None:
            self.logger.info("Process Ids not found in Redis")
            process_ids = self.supabase_handler.get_process_ids(process_id)
            if process_ids is None:
                raise Exception("Process Ids not found on Supabase")

            self.redis_handler.set_process_ids(process_ids)
        else:
            self.logger.info("Process Ids found in Redis")

        return process_ids

    def get_process_states(self, process_id: str) -> List[ProcessState]:
        process_states = self.redis_handler.get_process_states(process_id)

        if process_states is None:
            self.logger.info("Process States not found in Redis")
            process_states = self.supabase_handler.get_process_states(process_id)
            if process_states is None:
                raise Exception("Process States not found on Supabase")

            for process_state in process_states:
                self.redis_handler.create_process_state(process_id, process_state)
        else:
            self.logger.info("Process States found in Redis")
        return process_states

    def get_process_info(self, process_ids: ProcessIds) -> ProcessInfo:
        agent_data = self.get_agent_data(agent_id=process_ids.agent_id)
        process_data = self.get_process_data(process_id=process_ids.process_id)
        communications = self.get_communication_protocols(
            process_id=process_ids.process_id
        )
        process_states = self.get_process_states(process_id=process_ids.process_id)
        current_state = self.get_current_process_state(
            process_id=process_ids.process_id
        )

        return ProcessInfo(
            agent_data=agent_data,
            process_ids=process_ids,
            process_data=process_data,
            communications=communications,
            process_states=process_states,
            current_state=current_state,
        )

    def get_user_data(self, user_id: str) -> UserData:
        redis_handler = ClientHandlers().get_redis_handler()
        supabase_handler = ClientHandlers().get_supabase_handler()
        user_data = redis_handler.get_user_data(user_id)

        if user_data is None:
            self.logger.info("User data not found in Redis")
            # Fetch user profile from Supabase
            user_data = supabase_handler.get_user_data(user_id)
            if user_data is None:
                raise Exception("User data not found")

            # Store user data in redis
            redis_handler.set_user_data(user_data)
        else:
            self.logger.info("User data found in Redis")

        return user_data

    def get_request_service_data(self, service_id: str) -> RequestServiceData:
        request_service = self.redis_handler.get_request_service(service_id=service_id)

        if request_service is None:
            self.logger.info("Request Service not found in Redis")
            request_service = self.supabase_handler.get_request_service(service_id)
            if request_service is None:
                raise Exception("Request Service not found")

            self.redis_handler.create_request_service(request_service)

        return request_service.data

    def get_request(self, process_id: str) -> Optional[Request]:
        requests = self.redis_handler.get_requests(process_id=process_id)
        if len(requests) > 0:
            return requests[0]
        return None

    def get_request_format(self, service_id: str) -> RequestFormat:
        return self.supabase_handler.get_request_format(service_id)

    def publish(self, user_id: str, topic_name: str, content: str):
        self.supabase_handler.set_topic_content(
            user_id=user_id, name=topic_name, content=content
        )
        self.redis_handler.set_topic_content(
            user_id=user_id, topic_name=topic_name, content=content
        )

    def remove_active_agent(self, agent_id: str):
        self.redis_handler.remove_active_agent(agent_id=agent_id)
        self.supabase_handler.set_active_agent(agent_id=agent_id, active=False)

    def set_user_data(self, user_data: UserData):
        self.redis_handler.set_user_data(user_data)

    def set_event_notified(self, event: Event):
        event.status = EventStatus.NOTIFIED

        self.redis_handler.delete_event(event)
        self.supabase_handler.update_event(event)

    def set_request_completed(
        self, request: Request, success: bool, response: Dict[str, Any]
    ):
        request.data.response = response
        if success:
            request.data.status = RequestStatus.SUCCESS
        else:
            request.data.status = RequestStatus.FAILURE

        self.redis_handler.delete_request(request.id)
        self.supabase_handler.set_request_completed(request)

    def update_agent_data(self, agent_data: AgentData):
        try:
            self.supabase_handler.update_agent_data(agent_data)
            self.redis_handler.set_agent_data(agent_data)
            return "Success"
        except Exception as e:
            return f"Failure: {str(e)}"

    def update_current_process_state(
        self, process_id: str, process_state: ProcessState
    ):
        self.redis_handler.set_current_process_state(
            process_id=process_id, process_state=process_state
        )
        self.supabase_handler.update_current_process_state(
            process_id=process_id, process_state_id=process_state.id
        )

    def update_request_feedback(self, request: Request, feedback: str):
        request.data.feedback = feedback

        self.redis_handler.update_request(request)
        self.supabase_handler.update_request_feedback(request)

    def update_request_status(self, request: Request, status: RequestStatus):
        request.data.status = status

        self.redis_handler.update_request(request)
        self.supabase_handler.update_request_status(request)
