from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import DateTime, event
from sqlalchemy.orm import Mapped, ORMExecuteState, Session, with_loader_criteria
from sqlalchemy.testing.schema import mapped_column


@dataclass
class SoftDeleteMixin:
    """Mixin that provides a soft-delete timestamp column.

    Attributes:
        deleted_at (Mapped[datetime] | None): UTC timestamp (timezone-aware)
            indicating when the row was soft-deleted. A value of ``None``
            means the row is active.

    Usage:
        - Inherit from this mixin on ORM mapped classes to add a
          soft-delete column.
        - The module-level session listener will automatically filter
          out rows where ``deleted_at`` is non-null from SELECT queries.

    Example:
        class User(SoftDeleteMixin, Base):
            __tablename__ = "user"
            id: Mapped[int] = mapped_column(primary_key=True)

    """

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


@event.listens_for(Session, "do_orm_execute", propagate=True)
def _add_filtering_criteria(execute_state: ORMExecuteState) -> None:
    """Session-level event that applies soft-delete filtering to SELECTs.

    This listener inspects ORM execution state and, for SELECT statements
    (unless explicitly disabled), applies a loader criterion so that any
    mapped class that inherits ``SoftDeleteMixin`` will only load rows
    where ``deleted_at`` is ``None``.

    Args:
        execute_state (ORMExecuteState): The ORM execution state provided
            by SQLAlchemy when emitting the "do_orm_execute" event.

    Returns:
        None

    Notes:
        To bypass the automatic soft-delete filter for a particular
        execution, use:

            session.execute(stmt, execution_options={"skip_filter": True})

    """
    with_deleted = execute_state.execution_options.get("with_deleted", False)
    if execute_state.is_select and not with_deleted:
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                SoftDeleteMixin, lambda cls: cls.deleted_at.is_(None), include_aliases=True
            )
        )
