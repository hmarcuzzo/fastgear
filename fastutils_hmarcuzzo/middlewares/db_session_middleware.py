from contextvars import ContextVar

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from fastutils_hmarcuzzo.common.database.sqlalchemy.session import (
    AsyncDatabaseSessionFactory,
    SyncDatabaseSessionFactory,
)

# Unified context variable for both sync and async sessions
db_session: ContextVar[Session | AsyncSession | None] = ContextVar("db_session", default=None)


class BaseDBSessionMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        session_factory: SyncDatabaseSessionFactory | AsyncDatabaseSessionFactory,
    ) -> None:
        super().__init__(app)
        self.session_factory = session_factory


class SyncDBSessionMiddleware(BaseDBSessionMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Synchronous session management
        with self.session_factory.get_session() as session:
            db_session.set(session)
            response = await call_next(request)
            db_session.set(None)  # Clear the context variable after the request
        return response


class AsyncDBSessionMiddleware(BaseDBSessionMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Asynchronous session management
        async with self.session_factory.get_async_session() as session:
            db_session.set(session)
            response = await call_next(request)
            db_session.set(None)  # Clear the context variable after the request
        return response
