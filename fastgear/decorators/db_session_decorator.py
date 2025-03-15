import inspect
from collections.abc import Callable
from functools import wraps
from typing import TypeVar

from fastgear.common.database.sqlalchemy.session import (
    AsyncDatabaseSessionFactory,
    SyncDatabaseSessionFactory,
    db_session,
)

T = TypeVar("T", bound=Callable)


class DBSessionDecorator:
    def __init__(
        self, session_factory: SyncDatabaseSessionFactory | AsyncDatabaseSessionFactory
    ) -> None:
        self.session_factory = session_factory

    def __call__(self, func: T) -> T:
        is_coroutine = inspect.iscoroutinefunction(func)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            async with self.session_factory.get_session() as session:
                db_session.set(session)
                try:
                    return await func(*args, **kwargs)
                finally:
                    db_session.set(None)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with self.session_factory.get_session() as session:
                db_session.set(session)
                try:
                    return func(*args, **kwargs)
                finally:
                    db_session.set(None)

        return async_wrapper if is_coroutine else sync_wrapper
