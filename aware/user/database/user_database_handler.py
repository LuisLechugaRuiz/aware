from typing import Optional

from aware.database.client_handlers import ClientHandlers
from aware.user.user_data import UserData


class UserDatabaseHandler:
    def __init__(self):
        self.redis_client = ClientHandlers().get_redis_client()

    async def get_user_data(self, user_id: str) -> Optional[UserData]:
        data = await self.redis_client.get(f"user_data:{user_id}")
        if data:
            return UserData.from_json(data)
        return None

    async def get_api_key(self, user_id: str) -> Optional[str]:
        user_data = await self.get_user_data(user_id)
        if user_data:
            return user_data.api_key
        return None

    def set_user_data(self, user_data: UserData):
        self.redis_client.set(
            f"user_id:{user_data.user_id}:data",
            user_data.to_json(),
        )
