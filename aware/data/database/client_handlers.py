from supabase import create_client
import aioredis
import redis
import threading

from aware.agent.agent import Agent
from aware.memory.user.user_data import UserData
from aware.chat.conversation_schemas import JSONMessage
from aware.config.config import Config
from aware.data.database.supabase_handler.supabase_handler import SupabaseHandler
from aware.data.database.redis_handler.redis_handler import RedisHandler
from aware.data.database.redis_handler.async_redis_handler import AsyncRedisHandler
from aware.tools.tools import Tools
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

    # TODO: Implement me, it will be useful when users want to activate certain agents based on Tools!!
    def create_agent(self, user_id: str, tools_class: str):
        supabase_handlers = self.get_supabase_handler()
        agent = supabase_handlers.create_agent(user_id=user_id, tools_class=tools_class)
        redis_handlers = self.get_redis_handler()
        redis_handlers.create_agent(user_id=user_id, agent=agent)

    def get_supabase_handler(self):
        return self._instance.supabase_handler

    def get_async_redis_handler(self) -> AsyncRedisHandler:
        return self._instance.async_redis_handler

    def get_redis_handler(self) -> RedisHandler:
        return self._instance.redis_handler

    def get_tools(self, user_id: str, process_id: str) -> Tools:
        redis_handler = self.get_redis_handler()
        tools_class = redis_handler.get_tools_class(process_id)
        if tools_class is None:
            supabase_handler = self.get_supabase_handler()
            tools_class = supabase_handler.get_tools_class(process_id)
            redis_handler.set_tools_class(process_id, tools_class)
        tools_class = ToolsManager.get_tools(name=tools_class)
        if tools_class is None:
            raise Exception("Tools class not found")
        return tools_class(user_id=user_id, process_id=process_id)

    def get_agent_data(self, agent_id: str) -> Agent:
        redis_handler = self.get_redis_handler()
        agent_data = redis_handler.get_agent(agent_id)

        if agent_data is None:
            self.logger.info("Agent data not found in Redis")
            supabase_handler = self.get_supabase_handler()
            # Fetch agent data from Supabase
            agent_data = supabase_handler.get_agent(agent_id)
            if agent_data is None:
                raise Exception("Agent data not found")

            redis_handler.set_agent(agent_data)
        else:
            self.logger.info("Agent data found in Redis")

        return agent_data

    def get_user_data(self, user_id: str) -> UserData:
        redis_handler = self.get_redis_handler()
        user_data = redis_handler.get_user_data(user_id)

        if user_data is None:
            self.logger.info("User data not found in Redis")
            supabase_handler = self.get_supabase_handler()
            # Fetch user profile from Supabase
            user_profile = supabase_handler.get_user_profile(user_id)
            if user_profile is None:
                raise Exception("User profile not found")

            if not user_profile["initialized"]:
                try:
                    supabase_handler.initialize_user(user_id, user_profile)
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
            redis_handler.set_user_data(user_data)

            # Try to get assistant agent data from Redis otherwise get from Supabase
            # orchestrator_agent_data = self.get_agent_data(
            #     agent_id=user_profile["orchestrator_agent_id"]
            # )
        else:
            self.logger.info("User data found in Redis")

        return user_data
