from fastgear._internal.import_utils import has_extra, require_extra

from .controller_decorator import controller
from .pagination_with_search_decorator import PaginationWithSearchOptions
from .simple_pagination_decorator import SimplePaginationOptions

__all__ = [
    "PaginationWithSearchOptions",
    "SimplePaginationOptions",
    "controller",
]

_SQLALCHEMY_SYMBOLS = {"DBSessionDecorator"}

if has_extra("sqlalchemy"):
    from .db_session_decorator import DBSessionDecorator

    __all__ += ["DBSessionDecorator"]
else:

    def __getattr__(name: str):
        if name in _SQLALCHEMY_SYMBOLS:
            require_extra(name, "sqlalchemy")
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
