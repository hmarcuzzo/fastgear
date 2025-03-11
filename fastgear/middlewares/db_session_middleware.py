from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from fastgear.common.database.sqlalchemy.session import (
    AsyncDatabaseSessionFactory,
    SyncDatabaseSessionFactory,
)
from fastgear.variables import db_session


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
