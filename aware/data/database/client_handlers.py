from supabase import create_client
from redis import asyncio as aioredis
import redis
import threading
from typing import Dict, Optional

from aware.agent import AgentData
from aware.memory.user.user_data import UserData
from aware.chat.conversation_schemas import JSONMessage, ToolResponseMessage
from aware.config.config import Config
from aware.data.database.supabase_handler.supabase_handler import SupabaseHandler
from aware.data.database.redis_handler.redis_handler import RedisHandler
from aware.data.database.redis_handler.async_redis_handler import AsyncRedisHandler
from aware.process.process_data import ProcessData, ProcessIds
from aware.requests.request import Request
from aware.server.tasks import preprocess
from aware.tools.tools_manager import ToolsManager
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
        user_id: str,
        process_id: str,
        json_message: JSONMessage,
    ):
        redis_handlers = self.get_redis_handler()
        supabase_handlers = self.get_supabase_handler()
        self.logger.info("Adding to supa")
        chat_message = supabase_handlers.add_message(
            process_id=process_id,
            user_id=user_id,
            json_message=json_message,
        )
        self.logger.info("Adding to redis")
        redis_handlers.add_message(process_id=process_id, chat_message=chat_message)
        return chat_message

    # TODO: Implement me, it will be useful when users want to activate certain agents based on Tools!! - It should be module_name: system, main_prompt_name: (agent prompt name!!)
    def create_agent(
        self, user_id: str, module_name: str, main_prompt_name: str, tools_class: str
    ):
        agent = self.supabase_handler.create_agent(
            user_id, module_name, main_prompt_name, tools_class=tools_class
        )
        redis_handlers = self.get_redis_handler()
        redis_handlers.create_agent(user_id, agent=agent)

    # TODO: Move to Client? - Three classes: Service, Client and Request. (Async and Sync Clients!)
    def create_request(
        self,
        process_ids: ProcessIds,
        service_name: str,
        query: str,
        is_async: bool,
    ):
        request = self.supabase_handler.create_request(
            user_id=process_ids.user_id,
            client_process_id=process_ids.process_id,
            service_name=service_name,
            query=query,
            is_async=is_async,
        )

        service = self.redis_handler.get_service(service_id=request.service_id)
        self.redis_handler.create_request(
            service_process_id=service.process_id,
            service_id=request.service_id,
            request=request,
        )

        # Get agent id from process_id
        service_agent_id = self.redis_handler.get_agent_id_by_process_id(
            service.process_id
        )
        server_process_ids = ProcessIds(
            user_id=process_ids.user_id,
            agent_id=service_agent_id,
            process_id=service.process_id,
        )
        if not self.redis_handler.is_process_active(server_process_ids):
            # Start server process if not running
            preprocess.delay(process_ids)
        return request.id

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

    def get_process_data(self, process_ids: ProcessIds) -> ProcessData:
        process_data = self.redis_handler.get_process_data(process_ids)

        if process_data is None:
            self.logger.info("Process data not found in Redis")
            # Fetch process data from Supabase
            process_data = self.supabase_handler.get_process_data(process_ids)
            if process_data is None:
                raise Exception("Process data not found")

            self.redis_handler.set_process_data(process_data)
        else:
            self.logger.info("Process data found in Redis")

        return process_data

    def get_request(self, process_id: str) -> Optional[Request]:
        requests = self.redis_handler.get_requests(process_id=process_id)
        if len(requests) > 0:
            return requests[0]
        return None

    def get_user_data(self, user_id: str) -> UserData:
        user_data = self.redis_handler.get_user_data(user_id)

        if user_data is None:
            self.logger.info("User data not found in Redis")
            # Fetch user profile from Supabase
            user_profile = self.supabase_handler.get_user_profile(user_id)
            if user_profile is None:
                raise Exception("User profile not found")

            if not user_profile["initialized"]:
                try:
                    self.supabase_handler.initialize_user(user_id, user_profile)
                except Exception as e:
                    self.logger.error(f"Error while initializing user: {e}")
                    raise e

            # Store user data in redis
            user_data = UserData(
                user_id=user_id,
                user_name=user_profile["display_name"],
                api_key=user_profile["openai_api_key"],
                assistant_agent_id=user_profile["assistant_agent_id"],
                orchestrator_agent_id=user_profile["orchestrator_agent_id"],
            )
            self.redis_handler.set_user_data(user_data)

            # Try to get assistant agent data from Redis otherwise get from Supabase
            # orchestrator_agent_data = self.get_agent_data(
            #     agent_id=user_profile["orchestrator_agent_id"]
            # )
        else:
            self.logger.info("User data found in Redis")

        return user_data

    def initialize_user(self, user_id: str, user_profile: Dict[str, str]):
        self.supabase_handler.initialize_user(user_id, user_profile)
        # Now discover the services.
        services_data = ToolsManager(
            logger=FileLogger(name="migration_tests")
        ).discover_services()

        for tools_class, service_data in services_data.items():
            service = self.supabase_handler.create_service(
                user_id=user_id, tools_class=tools_class, service_data=service_data
            )
            self.redis_handler.set_service(service=service)
            self.redis_handler.set_topic_data(
                user_id=user_id,
                topic_name="user_name",
                topic_data=user_profile["display_name"],
            )

    def publish(self, user_id: str, topic_name: str, topic_data: str):
        self.supabase_handler.set_topic_content(
            user_id=user_id, name=topic_name, content=topic_data
        )
        self.redis_handler.set_topic_data(
            user_id=user_id, topic_name=topic_name, topic_data=topic_data
        )

    def remove_active_process(self, process_id: str):
        self.redis_handler.remove_active_process(process_id=process_id)
        self.supabase_handler.set_active_process(process_id=process_id, active=False)

    # TODO: This should:
    # - remove the request
    # - trigger new task to set the response as tool_ids.
    # - retrigger the client process.
    # TODO: Move to service?
    def set_request_completed(self, user_id: str, request: Request):
        # 1. Update request in Redis and Supabase
        self.redis_handler.update_request(request)
        self.supabase_handler.set_request_completed(request.id, request.data.response)

        # 2. Update last conversation message with the response.
        client_conversation_with_keys = self.redis_handler.get_conversation_with_keys(
            request.client_process_id
        )
        message_key, message = client_conversation_with_keys[-1]
        if not isinstance(message, ToolResponseMessage):
            raise ValueError("Last message is not a tool response message.")
        message.content = request.data.response
        self.redis_handler.update_message(message_key, message)

        # 3. Schedule client again using preprocess - Remove request from redis?
        # self.redis_handler.delete_request(request.id) ?? I think we should remove and notify, different reaction to async and sync. We should move this logic to service!!

        # TODO: Only if client is sync?
        agent_id = self.redis_handler.get_agent_id_by_process_id(
            request.client_process_id
        )
        process_ids = ProcessIds(
            user_id=user_id, agent_id=agent_id, process_id=request.client_process_id
        )
        preprocess.delay(process_ids.to_json())

    def update_agent_data(self, agent_data: AgentData):
        try:
            self.supabase_handler.update_agent_data(agent_data)
            self.redis_handler.set_agent_data(agent_data)
            return "Success"
        except Exception as e:
            return f"Failure: {str(e)}"
