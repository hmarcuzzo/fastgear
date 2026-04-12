from typing import TypeVar

from fastgear.common.database.sqlalchemy.base import Base

EntityType = TypeVar("EntityType", bound=Base)
