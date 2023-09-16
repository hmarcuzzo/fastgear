import re
import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Column, DateTime, event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils import UUIDType

from fastutils_hmarcuzzo.common.database.sqlalchemy.base import Base


@dataclass
class BaseEntity(Base):
    __abstract__ = True

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @declared_attr
    def __tablename__(self) -> str:
        """
            This method is used to generate the name of the table that will be created in the database for a given BaseEntity class.
        The table name is derived from the class name by converting it from CamelCase to snake_case.
        """
        return "_".join(re.findall("[A-Z][^A-Z]*", self.__name__)).lower()


@event.listens_for(BaseEntity, "before_insert", propagate=True)
def set_before_insert(mapper, connection, target: BaseEntity) -> None:
    if not target.created_at:
        target.created_at = datetime.utcnow()
    if not target.updated_at or target.updated_at < target.created_at:
        target.updated_at = target.created_at


@event.listens_for(BaseEntity, "before_update", propagate=True)
def set_before_update(mapper, connection, target: BaseEntity) -> None:
    target.updated_at = datetime.utcnow()
