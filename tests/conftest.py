from collections.abc import Generator

import pytest
from httpx import ASGITransport, AsyncClient

from tests.fixtures.api import app


@pytest.fixture(scope="session")
async def async_client() -> Generator[AsyncClient]:
    base_url = "http://test"
    transport = ASGITransport(app=app, raise_app_exceptions=False)

    async with AsyncClient(transport=transport, base_url=base_url) as async_client:
        yield async_client


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"
