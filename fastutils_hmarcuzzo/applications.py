import contextlib

from fastapi import FastAPI
from fastapi_pagination import add_pagination

from fastutils_hmarcuzzo.handlers.http_exceptions_handler import HttpExceptionsHandler
from fastutils_hmarcuzzo.middlewares.db_session_middleware import (
    AsyncDBSessionMiddleware,
    SyncDBSessionMiddleware,
)

UTILS_CALLABLES = {
    "http_exceptions_handler": lambda app, *args, **kwargs: HttpExceptionsHandler(app),
    "http_db_session_middleware": lambda app, *args, **kwargs: app.add_middleware(
        SyncDBSessionMiddleware, *args, **kwargs,
    ),
    "http_db_async_session_middleware": lambda app, *args, **kwargs: app.add_middleware(
        AsyncDBSessionMiddleware, *args, **kwargs,
    ),
    "pagination": lambda app, *args, **kwargs: add_pagination(app),
}


def apply_utils(app: FastAPI, utils: list[str], *args, **kwargs) -> None:
    for util in utils:
        with contextlib.suppress(KeyError):
            UTILS_CALLABLES[util](app, *args, **kwargs)
