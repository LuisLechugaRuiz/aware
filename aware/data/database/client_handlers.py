from supabase import create_client
import aioredis
import redis
import threading

from aware.memory.user.user_data import UserData
from aware.chat.conversation_schemas import JSONMessage
from aware.config.config import Config
from aware.data.database.supabase_handler.supabase_handler import SupabaseHandler
from aware.data.database.redis_handler.redis_handler import RedisHandler
from aware.data.database.redis_handler.async_redis_handler import AsyncRedisHandler
from aware.memory.memory_manager import MemoryManager
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
        self, chat_id: str, user_id: str, process_name: str, json_message: JSONMessage
    ):
        redis_handlers = self.get_redis_handler()
        supabase_handlers = self.get_supabase_handler()
        self.logger.info("Adding to supa")
        chat_message = supabase_handlers.add_message(
            chat_id=chat_id,
            user_id=user_id,
            process_name=process_name,
            json_message=json_message,
        )
        self.logger.info("Adding to redis")
        redis_handlers.add_message(
            chat_id=chat_id, chat_message=chat_message, process_name=process_name
        )
        return chat_message

    def get_supabase_handler(self):
        return self._instance.supabase_handler

    def get_async_redis_handler(self) -> AsyncRedisHandler:
        return self._instance.async_redis_handler

    def get_redis_handler(self) -> RedisHandler:
        return self._instance.redis_handler

    def get_user_data(self, user_id: str, chat_id: str) -> UserData:
        supabase_handler = self.get_supabase_handler()
        redis_handler = self.get_redis_handler()
        user_data = redis_handler.get_user_data(user_id)

        if user_data is None:
            self.logger.info("User data not found in Redis")
            # Fetch user profile from Supabase
            ui_profile = supabase_handler.get_ui_profile(user_id)
            if not ui_profile["has_topics"]:
                try:
                    self.logger.info("Creating topics")
                    # Create user on Weaviate
                    try:
                        memory_manager = MemoryManager(
                            user_id=user_id, logger=self.logger
                        )
                        result = memory_manager.create_user(
                            user_id=user_id, user_name=ui_profile["display_name"]
                        )
                    except Exception as e:
                        self.logger.error(f"Error while creating weaviate user: {e}")
                    if result.error:
                        self.logger.info(
                            f"DEBUG - error creating weaviate user result: {result.error}"
                        )
                    else:
                        self.logger.info(
                            f"DEBUG - success creating weaviate user result: {result.data}"
                        )
                    supabase_handler.create_topics(user_id)
                    self.logger.info("Updating user profile")
                    ui_profile["has_topics"] = True
                    supabase_handler.update_user_profile(user_id, ui_profile)
                except Exception as e:
                    self.logger.error(f"Error while creating topics: {e}")

            if ui_profile is None:
                raise Exception("User profile not found")
            user_data = UserData(
                chat_id=chat_id,
                user_id=user_id,
                user_name=ui_profile["display_name"],
                api_key=ui_profile["openai_api_key"],
            )
            # Store in Redis
            redis_handler.set_user_data(user_data)
        else:
            self.logger.info("User data found in Redis")

        return user_data
