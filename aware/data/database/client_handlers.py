from supabase import create_client
import aioredis
import redis
import threading

from aware.agent.memory.new_working_memory import WorkingMemory
from aware.config.config import Config
from aware.data.database.supabase_handler.supabase_handler import SupabaseHandler
from aware.data.database.redis_handler.redis_handler import RedisHandler
from aware.data.database.redis_handler.async_redis_handler import AsyncRedisHandler
from aware.utils.logger.file_logger import FileLogger
from aware.utils.helpers import get_current_date_iso8601


# TODO: Should we split between both clients? (Async and sync) - Async doesn't need to know about supabase
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
        self.async_redis_handler = AsyncRedisHandler(self.async_redis_client)
        self.logger = FileLogger("migration_client_handlers", should_print=True)

    def get_supabase_handler(self):
        return self._instance.supabase_handler

    def get_async_redis_handler(self) -> AsyncRedisHandler:
        return self._instance.async_redis_handler

    def get_redis_handler(self) -> RedisHandler:
        return self._instance.redis_handler

    def get_working_memory(self, user_id: str, chat_id: str) -> WorkingMemory:
        supabase_handler = self.get_supabase_handler()
        redis_handler = self.get_redis_handler()
        working_memory = redis_handler.get_working_memory(user_id)

        if working_memory is None:
            self.logger.info("Working memory not found in Redis")
            # Fetch user data from Supabase
            working_memory = supabase_handler.get_working_memory(user_id)
            user_profile = supabase_handler.get_user_profile(user_id)
            if user_profile is None:
                raise Exception("User profile not found")
            if working_memory is None:
                # Create empty working memory
                working_memory = WorkingMemory(
                    user_id=user_id,
                    chat_id=chat_id,
                    user_name=user_profile["display_name"],
                    thought="",
                    context="",
                    updated_at=get_current_date_iso8601(),
                )
                supabase_handler.set_working_memory(working_memory)
            # Store in Redis
            redis_handler.set_working_memory(working_memory)
            # Store user profile in Redis
            redis_handler.set_api_key(
                user_id, user_profile["openai_api_key"]
            )  # TODO: Get by model not only OpenAI
        else:
            self.logger.info("Working memory found in Redis")

        return working_memory
