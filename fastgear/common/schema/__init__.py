from fastgear._internal.import_utils import has_extra, require_extra

from .custom_base_model_schema import CustomBaseModel
from .exception_response_schema import DetailResponseSchema, ExceptionResponseSchema

__all__ = ["CustomBaseModel", "DetailResponseSchema", "ExceptionResponseSchema"]

_SQLALCHEMY_SYMBOLS = {"BaseSchema"}

if has_extra("sqlalchemy"):
    from .base_schema import BaseSchema

    __all__ += ["BaseSchema"]
else:

    def __getattr__(name: str):
        if name in _SQLALCHEMY_SYMBOLS:
            require_extra(name, "sqlalchemy")
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
