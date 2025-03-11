from contextvars import ContextVar

from fastgear.common.database.sqlalchemy.session import AllSessionType

# Unified context variable for both sync and async sessions
db_session: ContextVar[AllSessionType | None] = ContextVar("db_session", default=None)
