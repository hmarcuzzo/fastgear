import re
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped
from sqlalchemy.testing.schema import mapped_column
from sqlalchemy_utils import UUIDType
from uuid6 import uuid7

from fastgear.common.database.sqlalchemy.base import Base


@dataclass
class BaseEntity(Base):
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid7)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    @declared_attr
    def __tablename__(self) -> str:
        """Generates the name of the table that will be created in the database for a given BaseEntity class.

        The table name is derived from the class name by converting it from CamelCase to snake_case.

        Returns:
            str: The generated table name in snake_case.

        """
        return "_".join(re.findall("[A-Z][^A-Z]*", self.__name__)).lower()


@event.listens_for(BaseEntity, "before_insert", propagate=True)
def set_before_insert(mapper, connection, target: BaseEntity) -> None:
    """Event listener that sets the `created_at` and `updated_at` timestamps before inserting a new record.

    This function is triggered before a new `BaseEntity` record is inserted into the database.

    It ensures that the `created_at` and `updated_at` fields are set to the current datetime if they are not already
    set.

    Args:
        mapper: The SQLAlchemy mapper.
        connection: The database connection.
        target (BaseEntity): The instance of `BaseEntity` being inserted.

    """
    if not target.created_at:
        target.created_at = datetime.now()
    if not target.updated_at or target.updated_at < target.created_at:
        target.updated_at = target.created_at


@event.listens_for(BaseEntity, "before_update", propagate=True)
def set_before_update(mapper, connection, target: BaseEntity) -> None:
    target.updated_at = datetime.now()
