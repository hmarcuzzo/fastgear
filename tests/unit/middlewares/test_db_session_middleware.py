import asyncio
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from starlette.status import HTTP_200_OK

from fastgear.common.database.sqlalchemy.session import db_session
from fastgear.middlewares import DBSessionMiddleware
from tests.fixtures.middlewares.db_session_middleware_fixtures import (  # noqa: F401
    mock_async_session_factory,
    mock_call_next,
    mock_request,
    mock_sync_session_factory,
)

if TYPE_CHECKING:
    from starlette.responses import Response


@pytest.mark.describe("🧪 DBSessionMiddleware")
class TestDBSessionMiddleware:
    @pytest.mark.it("✅ Should handle sync session correctly")
    def test_sync_session_handling(
        self,
        mock_sync_session_factory: MagicMock,
        mock_request: MagicMock,
        mock_call_next: AsyncMock,
    ) -> None:
        app = FastAPI()
        middleware = DBSessionMiddleware(app, mock_sync_session_factory)

        # Mock the session manager to simulate a synchronous session
        mock_sync_session_factory.get_session.return_value = MagicMock()
        mock_session_manager = mock_sync_session_factory.get_session.return_value
        mock_session_manager.__enter__ = MagicMock(return_value="mock_session")
        mock_session_manager.__exit__ = MagicMock(return_value=None)

        # Ensure the session manager does not have async methods
        del mock_session_manager.__aenter__
        del mock_session_manager.__aexit__

        response: Response = asyncio.run(middleware.dispatch(mock_request, mock_call_next))

        assert response.status_code == HTTP_200_OK
        mock_sync_session_factory.get_session.assert_called_once()
        mock_call_next.assert_called_once_with(mock_request)
        assert db_session.get() is None

    @pytest.mark.asyncio
    @pytest.mark.it("✅ Should handle async session correctly")
    async def test_async_session_handling(
        self,
        mock_async_session_factory: MagicMock,
        mock_request: MagicMock,
        mock_call_next: AsyncMock,
    ) -> None:
        app = FastAPI()
        middleware = DBSessionMiddleware(app, mock_async_session_factory)

        response: Response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == HTTP_200_OK
        mock_async_session_factory.get_session.assert_called_once()
        mock_call_next.assert_called_once_with(mock_request)
        assert db_session.get() is None
