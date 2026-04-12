from typing import TypeVar

from pydantic import BaseModel

try:
    from fastgear.common.database.sqlalchemy.base import Base

    EntityType = TypeVar("EntityType", bound=Base)
except ImportError:
    EntityType = TypeVar("EntityType")  # type: ignore[assignment]

ColumnsQueryType = TypeVar("ColumnsQueryType", bound=type[BaseModel])
FindAllQueryType = TypeVar("FindAllQueryType", bound=type[BaseModel])
OrderByQueryType = TypeVar("OrderByQueryType", bound=type[BaseModel])
