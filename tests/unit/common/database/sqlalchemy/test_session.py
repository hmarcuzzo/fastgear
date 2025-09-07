from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fastgear.common.database.sqlalchemy.session import (
    AsyncDatabaseSessionFactory,
    SyncDatabaseSessionFactory,
)


@pytest.mark.describe("🧪  DatabaseSessionFactory")
class TestDatabaseSessionFactory:
    @pytest.mark.it("✅  SyncDatabaseSessionFactory should call create_engine and return a session")
    def test_sync_get_session_uses_sessionmaker(self):
        fake_engine = MagicMock(name="engine")
        fake_session = MagicMock(name="session")

        with (
            patch(
                "fastgear.common.database.sqlalchemy.session.create_engine",
                return_value=fake_engine,
            ) as create_engine,
            patch(
                "fastgear.common.database.sqlalchemy.session.sessionmaker",
                return_value=lambda: fake_session,
            ),
        ):
            factory = SyncDatabaseSessionFactory("sqlite:///test.db")

            create_engine.assert_called_once_with("sqlite:///test.db")

            sess = factory.get_session()
            assert sess is fake_session

    @pytest.mark.it(
        "✅  AsyncDatabaseSessionFactory should call create_async_engine and return an async sessionmaker"
    )
    def test_async_get_session_uses_async_sessionmaker(self):
        fake_async_engine = MagicMock(name="async_engine")
        fake_async_session = MagicMock(name="async_session")

        with (
            patch(
                "fastgear.common.database.sqlalchemy.session.create_async_engine",
                return_value=fake_async_engine,
            ) as create_async_engine,
            patch(
                "fastgear.common.database.sqlalchemy.session.async_sessionmaker",
                return_value=lambda: fake_async_session,
            ),
        ):
            factory = AsyncDatabaseSessionFactory("postgresql+asyncpg://test")

            create_async_engine.assert_called_once_with("postgresql+asyncpg://test")

            sess = factory.get_session()
            assert sess is fake_async_session

    @pytest.mark.asyncio
    @pytest.mark.it(
        "✅  AsyncDatabaseSessionFactory.close_engine should call dispose on the async engine"
    )
    async def test_async_close_engine_disposes(self):
        fake_async_engine = AsyncMock()
        fake_async_engine.dispose = AsyncMock()

        with patch(
            "fastgear.common.database.sqlalchemy.session.create_async_engine",
            return_value=fake_async_engine,
        ):
            factory = AsyncDatabaseSessionFactory("postgresql+asyncpg://test")
            await factory.close_engine()
            fake_async_engine.dispose.assert_awaited_once()
