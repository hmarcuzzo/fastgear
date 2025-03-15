import contextlib

from fastapi import FastAPI
from fastapi_pagination import add_pagination

from fastgear.handlers.http_exceptions_handler import HttpExceptionsHandler
from fastgear.middlewares.db_session_middleware import DBSessionMiddleware

UTILS_CALLABLES = {
    "http_exceptions_handler": lambda app, **kwargs: HttpExceptionsHandler(app, **kwargs),
    "http_db_session_middleware": lambda app, **kwargs: app.add_middleware(
        DBSessionMiddleware, **kwargs
    ),
    "pagination": lambda app: add_pagination(app),
}


def apply_utils(app: FastAPI, utils: list[str], **kwargs) -> None:
    for util in utils:
        with contextlib.suppress(KeyError):
            UTILS_CALLABLES[util](app, **kwargs)
