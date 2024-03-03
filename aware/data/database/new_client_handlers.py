from supabase import create_client
from redis import asyncio as aioredis
import redis
import threading

from aware.config.config import Config


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
        self.redis_client = redis.Redis(host="localhost", port=6379, db=0)
        self.async_redis_client = aioredis.from_url(
            "redis://localhost", encoding="utf-8", decode_responses=True
        )
        # self.redis_client.flushall()
        # self.async_redis_client.flushall()

    def get_supabase_client(self):
        return self.supabase_client

    def get_redis_client(self):
        return self.redis_client

    def get_async_redis_client(self):
        return self.async_redis_client
