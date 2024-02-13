from supabase import create_client
from redis import asyncio as aioredis
import redis
import threading
from typing import List, Optional

from aware.agent.agent_data import AgentData
from aware.chat.conversation_schemas import (
    JSONMessage,
)
from aware.communications.events.event import Event
from aware.communications.requests.request import Request
from aware.communications.requests.service import ServiceData
from aware.config.config import Config
from aware.data.database.supabase_handler.supabase_handler import SupabaseHandler
from aware.data.database.redis_handler.redis_handler import RedisHandler
from aware.data.database.redis_handler.async_redis_handler import AsyncRedisHandler
from aware.process.process_ids import ProcessIds
from aware.process.process_communications import ProcessCommunications
from aware.process.process_data import ProcessData
from aware.process.process_info import ProcessInfo
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

    def add_active_process(self, process_id: str):
        self.redis_handler.add_active_process(process_id)
        self.supabase_handler.set_active_process(process_id, active=True)

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
        tools_class: str,
        identity: str,
        task: str,
        instructions: str,
        thought_generator_mode: str,
    ) -> AgentData:
        self.logger.info("Creating agent")
        agent_data = self.supabase_handler.create_agent(
            user_id=user_id,
            name=name,
            tools_class=tools_class,
            identity=identity,
            task=task,
            instructions=instructions,
            thought_generator_mode=thought_generator_mode,
        )
        self.logger.info(f"Agent: {agent_data.id}, created on supabase")
        self.redis_handler.set_agent_data(agent_data)
        self.logger.info(f"Agent: {agent_data.id}, created on redis")
        return agent_data

    # TODO: Two kind of instructions:
    # Task Instructions (To specify how to perform the task).
    # Tool Instructions: To specify how to use the tool. ( docstring )
    def create_process(
        self,
        user_id: str,
        agent_id: str,
        name: str,
        tools_class: str,
        identity: str,
        task: str,
        instructions: str,
        service_name: Optional[str] = None,
    ) -> ProcessData:
        process_data = self.supabase_handler.create_process(
            user_id=user_id,
            agent_id=agent_id,
            name=name,
            tools_class=tools_class,
            identity=identity,
            task=task,
            instructions=instructions,
        )
        self.redis_handler.set_process_data(
            process_id=process_data.id, process_data=process_data
        )
        if service_name is None:
            service_name = name  # Use the name of the process, otherwise the name of the Agent. TODO: Solve this by internal and external requests.
        self.create_service(
            user_id=user_id, process_id=process_data.id, name=name, description=task
        )
        return process_data

    def create_event(self, user_id: str, event_name: str, content: str) -> Event:
        event = self.supabase_handler.create_event(
            user_id=user_id,
            event_name=event_name,
            content=content,
        )
        self.redis_handler.create_event(
            user_id=user_id,
            event=event,
        )
        return event

    def create_event_subscription(self, process_ids: ProcessIds, event_name: str):
        self.supabase_handler.create_event_subscription(process_ids, event_name)
        self.redis_handler.create_event_subscription(process_ids, event_name)
        self.logger.info(f"DEBUG - Created event subscription {event_name}")

    def create_request(
        self,
        process_ids: ProcessIds,
        service_name: str,
        query: str,
        is_async: bool,
    ) -> Request:
        request = self.supabase_handler.create_request(
            user_id=process_ids.user_id,
            client_process_id=process_ids.process_id,
            service_name=service_name,
            query=query,
            is_async=is_async,
        )
        self.redis_handler.create_request(
            service_process_id=request.service_process_id,
            service_id=request.service_id,
            request=request,
        )
        return request

    def create_service(
        self, user_id: str, process_id: str, name: str, description: str
    ):
        """Create new service"""
        service_data = ServiceData(name=name, description=description)
        service = self.supabase_handler.create_service(
            user_id=user_id, process_id=process_id, service_data=service_data
        )
        self.redis_handler.set_service(service=service)

    def create_topic_subscription(self, process_id: str, topic_name: str):
        topic_subscription = self.supabase_handler.create_topic_subscription(
            process_id, topic_name
        )
        self.redis_handler.create_topic_subscription(process_id, topic_subscription)
        self.logger.info(f"DEBUG - Created topic subscription {topic_name}")

    def create_topic(self, user_id: str, topic_name: str, topic_description: str):
        topic = self.supabase_handler.create_topic(
            user_id, topic_name, topic_description
        )
        self.redis_handler.create_topic(topic)
        self.logger.info(f"DEBUG - Created topic {topic_name}")

    # TODO: fetch from supabase as fallback
    def get_agent_id_by_process_id(self, process_id: str) -> str:
        return self.redis_handler.get_agent_id_by_process_id(process_id)

    def get_supabase_handler(self):
        return self._instance.supabase_handler

    def get_async_redis_handler(self) -> AsyncRedisHandler:
        return self._instance.async_redis_handler

    def get_redis_handler(self) -> RedisHandler:
        return self._instance.redis_handler

    def get_tools_class(self, process_id: str) -> str:
        redis_handler = self.get_redis_handler()
        tools_class = redis_handler.get_tools_class(process_id)
        if tools_class is None:
            supabase_handler = self.get_supabase_handler()
            tools_class = supabase_handler.get_tools_class(process_id)
            redis_handler.set_tools_class(process_id, tools_class)
        return tools_class

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

    def get_processes_ids_by_event(
        self, user_id: str, event: Event
    ) -> List[ProcessIds]:
        return self.redis_handler.get_processes_ids_by_event(user_id, event)

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

    def get_process_communications(self, process_id: str) -> ProcessCommunications:
        process_communications = self.redis_handler.get_process_communications(
            process_id=process_id,
        )

        if process_communications is None:
            self.logger.info("Process Communications not found in Redis")
            # Fetch agent data from Supabase
            process_communications = self.supabase_handler.get_process_communications(
                process_id=process_id
            )
            if process_communications is None:
                raise Exception("Process Communications not found on Supabase")

            self.redis_handler.set_process_communications(
                process_id=process_id, process_communications=process_communications
            )
        else:
            self.logger.info("Process Communications found in Redis")

        return process_communications

    def get_process_info(self, process_ids: ProcessIds) -> ProcessInfo:
        agent_data = self.get_agent_data(agent_id=process_ids.agent_id)
        process_data = self.get_process_data(process_id=process_ids.process_id)
        process_communications = self.get_process_communications(
            process_id=process_ids.process_id
        )
        return ProcessInfo(
            agent_data=agent_data,
            process_ids=process_ids,
            process_data=process_data,
            process_communications=process_communications,
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

    def get_request(self, process_id: str) -> Optional[Request]:
        requests = self.redis_handler.get_requests(process_id=process_id)
        if len(requests) > 0:
            return requests[0]
        return None

    def publish(self, user_id: str, topic_name: str, content: str):
        self.supabase_handler.set_topic_content(
            user_id=user_id, name=topic_name, content=content
        )
        self.redis_handler.set_topic_content(
            user_id=user_id, topic_name=topic_name, content=content
        )

    def remove_active_process(self, process_id: str):
        self.redis_handler.remove_active_process(process_id=process_id)
        self.supabase_handler.set_active_process(process_id=process_id, active=False)

    def send_feedback(self, request: Request):
        self.redis_handler.update_request(request)

    def set_user_data(self, user_data: UserData):
        self.redis_handler.set_user_data(user_data)

    def set_request_completed(self, request: Request):
        self.redis_handler.delete_request(request.id)
        self.supabase_handler.set_request_completed(request.id, request.data.response)

    def update_agent_data(self, agent_data: AgentData):
        try:
            self.supabase_handler.update_agent_data(agent_data)
            self.redis_handler.set_agent_data(agent_data)
            return "Success"
        except Exception as e:
            return f"Failure: {str(e)}"
