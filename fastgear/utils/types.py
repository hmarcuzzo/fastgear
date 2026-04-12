from typing import TypeVar

from pydantic import BaseModel

ColumnsQueryType = TypeVar("ColumnsQueryType", bound=type[BaseModel])
FindAllQueryType = TypeVar("FindAllQueryType", bound=type[BaseModel])
OrderByQueryType = TypeVar("OrderByQueryType", bound=type[BaseModel])
