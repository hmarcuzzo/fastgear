from unittest.mock import AsyncMock, MagicMock

import pytest

from fastgear.common.database.sqlalchemy.session import db_session
from fastgear.decorators.db_session_decorator import DBSessionDecorator


@pytest.mark.describe("🧪 DBSessionDecorator")
class TestDbSessionDecorator:
    @pytest.mark.it("✅ Should handle async function correctly")
    @pytest.mark.asyncio
    async def test_async_function_handling(self):
        mock_session_factory = MagicMock()
        mock_session_factory.get_session.return_value = MagicMock()
        mock_session = mock_session_factory.get_session.return_value
        mock_session.__aenter__ = AsyncMock(return_value="mock_session")
        mock_session.__aexit__ = AsyncMock(return_value=None)

        decorator = DBSessionDecorator(mock_session_factory)

        @decorator
        async def mock_async_function():
            assert db_session.get() == "mock_session"
            return "success"

        result = await mock_async_function()

        assert result == "success"
        mock_session.__aenter__.assert_called_once()
        mock_session.__aexit__.assert_called_once()
        assert db_session.get() is None

    @pytest.mark.it("✅ Should handle sync function correctly")
    def test_sync_function_handling(self):
        mock_session_factory = MagicMock()
        mock_session_factory.get_session.return_value = MagicMock()
        mock_session = mock_session_factory.get_session.return_value
        mock_session.__enter__ = MagicMock(return_value="mock_session")
        mock_session.__exit__ = MagicMock(return_value=None)

        decorator = DBSessionDecorator(mock_session_factory)

        @decorator
        def mock_sync_function():
            assert db_session.get() == "mock_session"
            return "success"

        result = mock_sync_function()

        assert result == "success"
        mock_session.__enter__.assert_called_once()
        mock_session.__exit__.assert_called_once()
        assert db_session.get() is None
