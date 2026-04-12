from .custom_base_model_schema import CustomBaseModel
from .exception_response_schema import DetailResponseSchema, ExceptionResponseSchema

__all__ = ["CustomBaseModel", "DetailResponseSchema", "ExceptionResponseSchema"]

try:
    from .base_schema import BaseSchema

    __all__ += ["BaseSchema"]
except ImportError:

    def __getattr__(name: str):
        if name == "BaseSchema":
            raise ImportError(
                "BaseSchema requires SQLAlchemy. Install it with: pip install fastgear[sqlalchemy]"
            )
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
