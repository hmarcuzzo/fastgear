import inspect

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from fastgear.common.database.sqlalchemy.session import (
    AsyncDatabaseSessionFactory,
    SyncDatabaseSessionFactory,
    db_session,
)


class DBSessionMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        session_factory: SyncDatabaseSessionFactory | AsyncDatabaseSessionFactory,
    ) -> None:
        super().__init__(app)
        self.session_factory = session_factory

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        session_manager = self.session_factory.get_session()
        is_async = inspect.iscoroutinefunction(session_manager.__aenter__)

        if is_async:
            async with session_manager as session:
                db_session.set(session)
                try:
                    return await call_next(request)
                finally:
                    db_session.set(None)
        else:
            with session_manager as session:
                db_session.set(session)
                try:
                    return await call_next(request)
                finally:
                    db_session.set(None)
