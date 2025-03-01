from typing import TypeVar

from pydantic import BaseModel

from fastutils_hmarcuzzo.common.database.sqlalchemy.base import Base

EntityType = TypeVar("EntityType", bound=Base)
ColumnsQueryType = TypeVar("ColumnsQueryType", bound=type[BaseModel])
