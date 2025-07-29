from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.requests import Request
from starlette.responses import Response


@pytest.fixture
def mock_sync_session_factory() -> MagicMock:
    factory = MagicMock()
    session_manager = MagicMock()
    factory.get_session.return_value = session_manager
    return factory


@pytest.fixture
def mock_async_session_factory() -> MagicMock:
    factory = MagicMock()
    session_manager = AsyncMock()
    factory.get_session.return_value = session_manager
    return factory


@pytest.fixture
def mock_request() -> MagicMock:
    return MagicMock(spec=Request)


@pytest.fixture
def mock_call_next() -> AsyncMock:
    async def _mock_call_next(request: Request) -> Response:
        return Response("OK")

    return AsyncMock(side_effect=_mock_call_next)
