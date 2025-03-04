from typing import TypeVar

from pydantic import BaseModel

from fastgear.common.database.sqlalchemy.base import Base

EntityType = TypeVar("EntityType", bound=Base)
ColumnsQueryType = TypeVar("ColumnsQueryType", bound=type[BaseModel])
