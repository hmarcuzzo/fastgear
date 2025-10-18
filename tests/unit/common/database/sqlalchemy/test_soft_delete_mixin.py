from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import Integer, String, create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, mapped_column

from fastgear.common.database.sqlalchemy.soft_delete_mixin import SoftDeleteMixin

Base = declarative_base()


class User(SoftDeleteMixin, Base):
    __tablename__ = "user"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String, nullable=False)


@pytest.fixture
def engine() -> Iterator[Engine]:
    """Create a fresh in-memory SQLite engine and create tables for each test."""
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.mark.describe("🧪  SoftDeleteMixin")
class TestSoftDeleteMixin:
    @pytest.mark.it("✅  Should have a 'deleted_at' column")
    def test_it_has_deleted_at_column(self) -> None:
        assert hasattr(User, "deleted_at")

    @pytest.mark.it("✅  Should exclude soft-deleted records by default")
    def test_it_excludes_deleted_by_default(self, engine: Engine) -> None:
        with Session(engine) as session:
            # User is mapped with a dataclass mixin; construct without kwargs
            active = User()
            active.name = "active"
            active.deleted_at = None

            deleted = User()
            deleted.name = "deleted"

            deleted.deleted_at = datetime.now(UTC)
            session.add_all([active, deleted])
            session.commit()

            results = session.execute(select(User)).scalars().all()
            names = [u.name for u in results]

            assert names == ["active"]

    @pytest.mark.it("✅  Should include soft-deleted records when with_deleted is set")
    def test_it_includes_deleted_when_with_deleted(self, engine: Engine) -> None:
        with Session(engine) as session:
            active = User()
            active.name = "active"
            active.deleted_at = None

            deleted = User()
            deleted.name = "deleted"
            deleted.deleted_at = datetime.now(UTC)

            session.add_all([active, deleted])
            session.commit()

            stmt = select(User).execution_options(with_deleted=True)
            results = session.execute(stmt).scalars().all()
            names = sorted([u.name for u in results])

            assert names == ["active", "deleted"]
