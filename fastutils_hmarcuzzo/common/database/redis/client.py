import redis.asyncio as aioredis
from redis.asyncio import Redis


class RedisClientFactory:
    """Factory class for creating and managing Redis client connections using an asynchronous connection pool.

    Args:
        redis_url (str): The URL of the Redis server.

    """

    def __init__(self, redis_url: str) -> None:
        self.pool = aioredis.ConnectionPool.from_url(redis_url)

    def get_client(self) -> Redis:
        """Retrieves a Redis client instance from the connection pool.

        Returns:
            Redis: An instance of the Redis client.

        """
        return aioredis.Redis(connection_pool=self.pool)

    async def close_pool(self) -> None:
        """Closes the connection pool asynchronously.

        Returns:
            None

        """
        await self.pool.aclose()
