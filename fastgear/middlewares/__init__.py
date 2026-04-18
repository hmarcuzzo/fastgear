from fastgear._internal.import_utils import has_extra, require_extra

__all__ = []

_SQLALCHEMY_SYMBOLS = {"DBSessionMiddleware"}

if has_extra("sqlalchemy"):
    from .db_session_middleware import DBSessionMiddleware

    __all__ += ["DBSessionMiddleware"]
else:

    def __getattr__(name: str):
        if name in _SQLALCHEMY_SYMBOLS:
            require_extra(name, "sqlalchemy")
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
