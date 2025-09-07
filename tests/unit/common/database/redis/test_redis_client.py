from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fastgear.common.database.redis.client import RedisClientFactory


@pytest.mark.describe("🧪  RedisClientFactory")
class TestRedisClientFactory:
    @pytest.mark.it("✅  Should use ConnectionPool.from_url and pass pool to Redis")
    def test_get_client_uses_same_pool(self):
        fake_pool = MagicMock(name="pool")

        with patch(
            "fastgear.common.database.redis.client.aioredis.ConnectionPool.from_url",
            return_value=fake_pool,
        ) as from_url:
            factory = RedisClientFactory("redis://localhost:6379/0")

            # ensure from_url was called with the provided URL
            from_url.assert_called_once_with("redis://localhost:6379/0")

            # patch Redis to observe it receives the same pool
            with patch(
                "fastgear.common.database.redis.client.aioredis.Redis",
                return_value=MagicMock(name="redis"),
            ) as redis_cls:
                client = factory.get_client()
                redis_cls.assert_called_once_with(connection_pool=fake_pool)
                assert client is not None

    @pytest.mark.asyncio
    @pytest.mark.it("✅  Should await pool.aclose when closing the pool")
    async def test_close_pool_calls_aclose(self):
        fake_pool = AsyncMock()
        # aclose should be awaitable
        fake_pool.aclose = AsyncMock()

        with patch(
            "fastgear.common.database.redis.client.aioredis.ConnectionPool.from_url",
            return_value=fake_pool,
        ):
            factory = RedisClientFactory("redis://example/1")

            # call close_pool and ensure pool.aclose was awaited
            await factory.close_pool()
            fake_pool.aclose.assert_awaited_once()
