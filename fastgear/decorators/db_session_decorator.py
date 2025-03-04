import asyncio
import inspect
from collections.abc import Callable
from contextvars import ContextVar
from functools import wraps

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from fastgear.common.database.sqlalchemy.session import (
    AsyncDatabaseSessionFactory,
    SyncDatabaseSessionFactory,
)

# Unified context variable for both sync and async sessions
db_session: ContextVar[Session | AsyncSession | None] = ContextVar("db_session", default=None)


class BaseDBSessionDecorator:
    def __init__(
        self, session_factory: SyncDatabaseSessionFactory | AsyncDatabaseSessionFactory
    ) -> None:
        self.session_factory = session_factory


# Decorator for synchronous session management
class SyncDBSessionDecorator(BaseDBSessionDecorator):
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with self.session_factory.get_session() as session:
                db_session.set(session)
                try:
                    if inspect.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    # Run the synchronous function in a thread pool executor
                    return await asyncio.to_thread(func, *args, **kwargs)
                finally:
                    db_session.set(None)  # Clear the context variable after the request

        return wrapper


# Decorator for asynchronous session management
class AsyncDBSessionDecorator(BaseDBSessionDecorator):
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with self.session_factory.get_async_session() as session:
                db_session.set(session)
                try:
                    return await func(*args, **kwargs)
                finally:
                    db_session.set(None)  # Clear the context variable after the request

        return wrapper
