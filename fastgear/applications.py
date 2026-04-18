from fastapi import FastAPI
from fastapi_pagination import add_pagination

from fastgear._internal.import_utils import has_extra, require_extra
from fastgear.handlers import HttpExceptionsHandler

UTILS_CALLABLES = {
    "http_exceptions_handler": HttpExceptionsHandler,
    "pagination": lambda app, **kwargs: add_pagination(app),
}

if has_extra("sqlalchemy"):
    from fastgear.middlewares import DBSessionMiddleware

    UTILS_CALLABLES["http_db_session_middleware"] = lambda app, **kwargs: app.add_middleware(
        DBSessionMiddleware, **kwargs
    )


_SQLALCHEMY_UTILS = {"http_db_session_middleware"}


def apply_utils(app: FastAPI, utils: list[str], **kwargs) -> None:
    for util in utils:
        if util not in UTILS_CALLABLES:
            if util in _SQLALCHEMY_UTILS:
                require_extra(util, "sqlalchemy")
            continue
        UTILS_CALLABLES[util](app, **kwargs)
