from datetime import datetime, timezone

import pytest
from sqlalchemy import DateTime, ForeignKey, Integer, String, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, mapped_column

from fastgear.common.database.sqlalchemy.repository_utils.base_repository_utils import (
    BaseRepositoryUtils,
)
from tests.fixtures.common.sqlalchemy_fixtures import UpdateSchema, engine


@pytest.mark.describe("🧪  BaseRepositoryUtils")
class TestBaseRepositoryUtils:
    @pytest.mark.it("✅  should_be_updated returns False when no fields set in update schema")
    def test_returns_false_when_unset(self) -> None:
        class Entity:
            name = "Alice"
            age = 30

        assert BaseRepositoryUtils.should_be_updated(Entity(), UpdateSchema()) is False

    @pytest.mark.it("✅  should_be_updated returns False when values are unchanged")
    def test_returns_false_when_values_unchanged(self) -> None:
        class Entity:
            name = "Alice"
            age = 30

        schema = UpdateSchema(name="Alice")
        assert BaseRepositoryUtils.should_be_updated(Entity(), schema) is False

    @pytest.mark.it("✅  should_be_updated returns True when any value changes")
    def test_returns_true_when_any_value_changes(self) -> None:
        class Entity:
            name = "Alice"
            age = 30

        schema = UpdateSchema(age=31)
        assert BaseRepositoryUtils.should_be_updated(Entity(), schema) is True

    @pytest.mark.it(
        "✅  soft_delete_cascade_from_parent soft-deletes parent and cascades to child tables with deleted_at column"
    )
    def test_cascade_soft_delete_happy_path(self, engine: Engine) -> None:
        Base = declarative_base()

        class Parent(Base):
            __tablename__ = "parent"
            id = mapped_column(Integer, primary_key=True)
            name = mapped_column(String, nullable=False)
            deleted_at = mapped_column(DateTime(timezone=True), nullable=True)

        class ChildWithDeleted(Base):
            __tablename__ = "child_with_deleted"
            id = mapped_column(Integer, primary_key=True)
            parent_id = mapped_column(ForeignKey("parent.id", ondelete="CASCADE"), nullable=False)
            value = mapped_column(String, nullable=False)
            deleted_at = mapped_column(DateTime(timezone=True), nullable=True)

        class ChildNoDeleted(Base):
            __tablename__ = "child_no_deleted"
            id = mapped_column(Integer, primary_key=True)
            parent_id = mapped_column(ForeignKey("parent.id", ondelete="CASCADE"), nullable=False)
            value = mapped_column(String, nullable=False)
            # intentionally no deleted_at column

        Base.metadata.create_all(engine)

        with Session(engine) as session:
            session.add_all(
                [
                    Parent(id=1, name="p1", deleted_at=None),
                    ChildWithDeleted(id=10, parent_id=1, value="c1", deleted_at=None),
                    ChildWithDeleted(id=11, parent_id=1, value="c2", deleted_at=None),
                    ChildNoDeleted(id=20, parent_id=1, value="n1"),
                ]
            )
            session.commit()

            # run
            result = BaseRepositoryUtils.soft_delete_cascade_from_parent(
                Parent, parent_entity_id=1, db=session
            )

            # parent should be marked deleted
            parent = session.execute(select(Parent).where(Parent.id == 1)).scalar_one()
            assert parent.deleted_at is not None
            assert isinstance(parent.deleted_at, datetime)

            # children with deleted_at should be marked as well
            rows = session.execute(select(ChildWithDeleted)).scalars().all()
            assert all(r.deleted_at is not None for r in rows)
            assert all(isinstance(r.deleted_at, datetime) for r in rows)

            # child without deleted_at remains unchanged
            no_del = session.execute(select(ChildNoDeleted)).scalars().all()
            assert len(no_del) == 1

            # response assertions
            assert isinstance(result["affected"], int)
            # 1 for parent + 2 for ChildWithDeleted rows
            assert result["affected"] >= 3
            assert {"table": "parent", "id": 1} in result["raw"]
            # generated_maps contains the traversal order: starts with parent
            assert "parent" in result["generated_maps"][0]
            assert "child_with_deleted" in result["generated_maps"][0]

    @pytest.mark.it(
        "❌  soft_delete_cascade_from_parent raises when parent has no deleted_at column"
    )
    def test_raises_when_parent_missing_deleted_at(self, engine: Engine) -> None:
        Base = declarative_base()

        class ParentNoDeleted(Base):
            __tablename__ = "parent_no_deleted"
            id = mapped_column(Integer, primary_key=True)
            name = mapped_column(String, nullable=False)
            # no deleted_at

        Base.metadata.create_all(engine)

        with Session(engine) as session:
            with pytest.raises(
                ValueError, match='Parent entity "ParentNoDeleted" has no "deleted_at" column'
            ) as exc:
                BaseRepositoryUtils.soft_delete_cascade_from_parent(
                    ParentNoDeleted, parent_entity_id=1, db=session
                )
            assert 'has no "deleted_at" column' in str(exc.value)

    @pytest.mark.it(
        "❌  soft_delete_cascade_from_parent raises when parent has composite primary key"
    )
    def test_raises_when_composite_primary_key(self, engine: Engine) -> None:
        Base = declarative_base()

        class ParentCompositePK(Base):
            __tablename__ = "parent_composite_pk"
            a_id = mapped_column(Integer, primary_key=True)
            b_id = mapped_column(Integer, primary_key=True)
            deleted_at = mapped_column(DateTime(timezone=True), nullable=True)

        Base.metadata.create_all(engine)

        with Session(engine) as session:
            with pytest.raises(ValueError, match="Composite primary keys are not supported") as exc:
                BaseRepositoryUtils.soft_delete_cascade_from_parent(
                    ParentCompositePK, parent_entity_id="1", db=session
                )
            assert "Composite primary keys are not supported" in str(exc.value)

    @pytest.mark.it(
        "✅  soft_delete_cascade_from_parent skips re-processing the same child table when it appears multiple times (child in visited)"
    )
    def test_skips_child_already_visited_with_multiple_fks(self, engine: Engine) -> None:
        Base = declarative_base()

        class Parent(Base):
            __tablename__ = "parent_multi_fk"
            id = mapped_column(Integer, primary_key=True)
            deleted_at = mapped_column(DateTime(timezone=True), nullable=True)

        class ChildDoubleFK(Base):
            __tablename__ = "child_double_fk"
            id = mapped_column(Integer, primary_key=True)
            parent_id1 = mapped_column(ForeignKey("parent_multi_fk.id"), nullable=False)
            parent_id2 = mapped_column(ForeignKey("parent_multi_fk.id"), nullable=False)
            deleted_at = mapped_column(DateTime(timezone=True), nullable=True)

        Base.metadata.create_all(engine)

        with Session(engine) as session:
            session.add(Parent(id=1, deleted_at=None))
            session.add(ChildDoubleFK(id=100, parent_id1=1, parent_id2=1, deleted_at=None))
            session.commit()

            result = BaseRepositoryUtils.soft_delete_cascade_from_parent(
                Parent, parent_entity_id=1, db=session
            )

            # parent marked
            parent = session.execute(select(Parent).where(Parent.id == 1)).scalar_one()
            assert parent.deleted_at is not None

            # child updated once, despite two FK edges
            child = session.execute(
                select(ChildDoubleFK).where(ChildDoubleFK.id == 100)
            ).scalar_one()
            assert child.deleted_at is not None

            # affected should be exactly 2: 1 parent + 1 child
            assert result["affected"] == 2

            # child table name should appear only once in generated_maps
            tables = result["generated_maps"][0]
            assert tables.count("child_double_fk") == 1

    @pytest.mark.it(
        "✅  soft_delete_cascade_from_parent does not enqueue child when no rows were updated (rowcount == 0)"
    )
    def test_does_not_enqueue_child_when_rowcount_zero(self, engine: Engine) -> None:
        Base = declarative_base()

        class Parent(Base):
            __tablename__ = "parent_rowcount_zero"
            id = mapped_column(Integer, primary_key=True)
            deleted_at = mapped_column(DateTime(timezone=True), nullable=True)

        class ChildWithDeleted(Base):
            __tablename__ = "child_with_deleted_zero"
            id = mapped_column(Integer, primary_key=True)
            parent_id = mapped_column(ForeignKey("parent_rowcount_zero.id"), nullable=False)
            deleted_at = mapped_column(DateTime(timezone=True), nullable=True)

        Base.metadata.create_all(engine)

        with Session(engine) as session:
            # Child already marked as deleted -> UPDATE matches zero rows
            already = datetime.now(timezone.utc)
            session.add(Parent(id=1, deleted_at=None))
            session.add(ChildWithDeleted(id=10, parent_id=1, deleted_at=already))
            session.commit()

            result = BaseRepositoryUtils.soft_delete_cascade_from_parent(
                Parent, parent_entity_id=1, db=session
            )

            # Parent gets marked deleted
            parent = session.execute(select(Parent).where(Parent.id == 1)).scalar_one()
            assert parent.deleted_at is not None

            # Child remains with its existing deleted_at and was not enqueued for next frontier
            child = session.execute(
                select(ChildWithDeleted).where(ChildWithDeleted.id == 10)
            ).scalar_one()
            assert child.deleted_at.replace(tzinfo=None) == already.replace(tzinfo=None)

            # Only 1 affected (the parent). Child update matched 0 rows -> rowcount == 0
            assert result["affected"] == 1

            # generated_maps should only contain the parent table name
            tables = result["generated_maps"][0]
            assert tables == ["parent_rowcount_zero"]
