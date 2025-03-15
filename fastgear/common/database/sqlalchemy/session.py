from abc import ABC, abstractmethod
from contextvars import ContextVar

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncSessionTransaction,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, SessionTransaction, sessionmaker

SyncSessionType = Session | SessionTransaction
AsyncSessionType = AsyncSession | AsyncSessionTransaction
AllSessionType = SyncSessionType | AsyncSessionType

# Unified context variable for both sync and async sessions
db_session: ContextVar[AllSessionType | None] = ContextVar("db_session", default=None)


class AbstractDatabaseSessionFactory(ABC):
    def __init__(self) -> None:
        """Initializes the DatabaseSessionFactory with the given database URL."""

    @abstractmethod
    def get_session(self) -> Session | AsyncSession:
        """Creates a new database session.

        Returns:
            SyncSessionType: A new SQLAlchemy session.
        """


class SyncDatabaseSessionFactory(AbstractDatabaseSessionFactory):
    def __init__(self, database_url: str) -> None:
        """Initializes the DatabaseSessionFactory with the given database URL.

        Args:
            database_url (str): The URL of the database to connect to.
        """
        super().__init__()
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(
            self.engine, autocommit=False, autoflush=False, expire_on_commit=False
        )

    def get_session(self) -> Session:
        """Creates a new database session.

        Returns:
            Session: A new SQLAlchemy session.

        """
        return self.SessionLocal()


class AsyncDatabaseSessionFactory(AbstractDatabaseSessionFactory):
    def __init__(self, database_url: str) -> None:
        """Initializes the AsyncDatabaseSessionFactory with the given database URL.

        Args:
            database_url (str): The URL of the database to connect to.
        """
        super().__init__()
        self.async_engine = create_async_engine(database_url)
        self.AsyncSessionLocal = async_sessionmaker(
            self.async_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            class_=AsyncSession,
        )

    def get_session(self) -> AsyncSession:
        """Creates a new asynchronous database session.

        Returns:
            AsyncSession: A new SQLAlchemy asynchronous session.
        """
        return self.AsyncSessionLocal()

    async def close_engine(self) -> None:
        """Closes the asynchronous database engine.

        This method should be called to properly dispose of the engine and release any resources.
        """
        await self.async_engine.dispose()
