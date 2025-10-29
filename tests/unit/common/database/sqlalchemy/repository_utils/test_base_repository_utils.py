from datetime import UTC, datetime

import pytest
from sqlalchemy import DateTime, ForeignKey, Integer, String, select
from sqlalchemy.orm import Session, declarative_base, mapped_column

from fastgear.common.database.sqlalchemy.repository_utils.base_repository_utils import (
    BaseRepositoryUtils,
)
from fastgear.types.http_exceptions import NotFoundException
from tests.fixtures.common.sqlalchemy_fixtures import UpdateSchema, engine

Base = declarative_base()


class Parent(Base):
    __tablename__ = "parents"

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(50))
    deleted_at = mapped_column(DateTime, nullable=True)


class Child(Base):
    __tablename__ = "children"

    id = mapped_column(Integer, primary_key=True)
    parent_id = mapped_column(Integer, ForeignKey("parents.id"))
    name = mapped_column(String(50))
    deleted_at = mapped_column(DateTime, nullable=True)


class GrandChild(Base):
    __tablename__ = "grandchildren"

    id = mapped_column(Integer, primary_key=True)
    child_id = mapped_column(Integer, ForeignKey("children.id"))
    name = mapped_column(String(50))
    deleted_at = mapped_column(DateTime, nullable=True)


class ChildWithoutSoftDelete(Base):
    __tablename__ = "children_no_soft_delete"

    id = mapped_column(Integer, primary_key=True)
    parent_id = mapped_column(Integer, ForeignKey("parents.id"))
    name = mapped_column(String(50))


class ParentWithoutSoftDelete(Base):
    __tablename__ = "parents_no_soft_delete"

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(50))


class ParentCompositeKey(Base):
    __tablename__ = "parents_composite"

    id1 = mapped_column(Integer, primary_key=True)
    id2 = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(50))
    deleted_at = mapped_column(DateTime, nullable=True)


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


@pytest.mark.describe("🧪  BaseRepositoryUtils.soft_delete_cascade_from_parent")
class TestSoftDeleteCascadeFromParent:
    @pytest.fixture
    def db_session(self, engine):
        Base.metadata.create_all(engine)
        session = Session(engine)
        yield session
        session.close()
        Base.metadata.drop_all(engine)

    @pytest.mark.it("✅  raises ValueError when parent entity has no deleted_at column")
    def test_raises_when_no_deleted_at_column(self, db_session) -> None:
        with pytest.raises(ValueError, match='has no "deleted_at" column'):
            BaseRepositoryUtils.soft_delete_cascade_from_parent(
                ParentWithoutSoftDelete,
                update_filter="1",
                db=db_session,
            )

    @pytest.mark.it("✅  raises ValueError when entity has composite primary key")
    def test_raises_when_composite_primary_key(self, db_session) -> None:
        with pytest.raises(ValueError, match="Composite primary keys are not supported"):
            BaseRepositoryUtils.soft_delete_cascade_from_parent(
                ParentCompositeKey,
                update_filter="1",
                db=db_session,
            )

    @pytest.mark.it("✅  raises NotFoundException when no entity matches filter")
    def test_raises_when_no_entity_found(self, db_session) -> None:
        with pytest.raises(NotFoundException, match="Could not find any entity"):
            BaseRepositoryUtils.soft_delete_cascade_from_parent(
                Parent,
                update_filter="999",
                db=db_session,
            )

    @pytest.mark.it("✅  soft deletes parent entity by string id")
    def test_soft_deletes_parent_by_id(self, db_session) -> None:
        parent = Parent(id=1, name="Parent1")
        db_session.add(parent)
        db_session.commit()

        result = BaseRepositoryUtils.soft_delete_cascade_from_parent(
            Parent,
            update_filter="1",
            db=db_session,
        )

        assert result["affected"] == 1
        assert len(result["raw"]) == 1
        assert result["raw"][0].deleted_at is not None

        db_session.expire_all()
        updated_parent = db_session.get(Parent, 1)
        assert updated_parent.deleted_at is not None

    @pytest.mark.it("✅  soft deletes parent entity by UpdateOptions filter")
    def test_soft_deletes_parent_by_update_options(self, db_session) -> None:
        parent = Parent(id=1, name="Parent1")
        db_session.add(parent)
        db_session.commit()

        result = BaseRepositoryUtils.soft_delete_cascade_from_parent(
            Parent,
            update_filter={"where": [Parent.name == "Parent1"]},
            db=db_session,
        )

        assert result["affected"] == 1
        db_session.expire_all()
        updated_parent = db_session.get(Parent, 1)
        assert updated_parent.deleted_at is not None

    @pytest.mark.it("✅  does not soft delete already deleted parent")
    def test_does_not_delete_already_deleted_parent(self, db_session) -> None:
        parent = Parent(id=1, name="Parent1", deleted_at=datetime.now(UTC))
        db_session.add(parent)
        db_session.commit()

        with pytest.raises(NotFoundException):
            BaseRepositoryUtils.soft_delete_cascade_from_parent(
                Parent,
                update_filter="1",
                db=db_session,
            )

    @pytest.mark.it("✅  cascades soft delete to direct children")
    def test_cascades_to_direct_children(self, db_session) -> None:
        parent = Parent(id=1, name="Parent1")
        child1 = Child(id=1, parent_id=1, name="Child1")
        child2 = Child(id=2, parent_id=1, name="Child2")

        db_session.add_all([parent, child1, child2])
        db_session.commit()

        result = BaseRepositoryUtils.soft_delete_cascade_from_parent(
            Parent,
            update_filter="1",
            db=db_session,
        )

        assert result["affected"] == 3

        db_session.expire_all()
        updated_parent = db_session.get(Parent, 1)
        updated_child1 = db_session.get(Child, 1)
        updated_child2 = db_session.get(Child, 2)

        assert updated_parent.deleted_at is not None
        assert updated_child1.deleted_at is not None
        assert updated_child2.deleted_at is not None

    @pytest.mark.it("✅  cascades soft delete to multiple levels (grandchildren)")
    def test_cascades_to_grandchildren(self, db_session) -> None:
        parent = Parent(id=1, name="Parent1")
        child = Child(id=1, parent_id=1, name="Child1")
        grandchild1 = GrandChild(id=1, child_id=1, name="GrandChild1")
        grandchild2 = GrandChild(id=2, child_id=1, name="GrandChild2")

        db_session.add_all([parent, child, grandchild1, grandchild2])
        db_session.commit()

        result = BaseRepositoryUtils.soft_delete_cascade_from_parent(
            Parent,
            update_filter="1",
            db=db_session,
        )

        assert result["affected"] == 4

        db_session.expire_all()
        updated_parent = db_session.get(Parent, 1)
        updated_child = db_session.get(Child, 1)
        updated_grandchild1 = db_session.get(GrandChild, 1)
        updated_grandchild2 = db_session.get(GrandChild, 2)

        assert updated_parent.deleted_at is not None
        assert updated_child.deleted_at is not None
        assert updated_grandchild1.deleted_at is not None
        assert updated_grandchild2.deleted_at is not None

    @pytest.mark.it("✅  does not cascade to already soft deleted children")
    def test_does_not_cascade_to_already_deleted_children(self, db_session) -> None:
        parent = Parent(id=1, name="Parent1")
        child = Child(id=1, parent_id=1, name="Child1", deleted_at=datetime.now(UTC))

        db_session.add_all([parent, child])
        db_session.commit()

        result = BaseRepositoryUtils.soft_delete_cascade_from_parent(
            Parent,
            update_filter="1",
            db=db_session,
        )

        assert result["affected"] == 1

        db_session.expire_all()
        updated_parent = db_session.get(Parent, 1)
        assert updated_parent.deleted_at is not None

    @pytest.mark.it("✅  does not affect children of other parents")
    def test_does_not_affect_other_parents_children(self, db_session) -> None:
        parent1 = Parent(id=1, name="Parent1")
        parent2 = Parent(id=2, name="Parent2")
        child1 = Child(id=1, parent_id=1, name="Child1")
        child2 = Child(id=2, parent_id=2, name="Child2")

        db_session.add_all([parent1, parent2, child1, child2])
        db_session.commit()

        result = BaseRepositoryUtils.soft_delete_cascade_from_parent(
            Parent,
            update_filter="1",
            db=db_session,
        )

        assert result["affected"] == 2

        db_session.expire_all()
        updated_parent1 = db_session.get(Parent, 1)
        updated_parent2 = db_session.get(Parent, 2)
        updated_child1 = db_session.get(Child, 1)
        updated_child2 = db_session.get(Child, 2)

        assert updated_parent1.deleted_at is not None
        assert updated_parent2.deleted_at is None
        assert updated_child1.deleted_at is not None
        assert updated_child2.deleted_at is None

    @pytest.mark.it("✅  skips children tables without deleted_at column")
    def test_skips_children_without_deleted_at(self, db_session) -> None:
        parent = Parent(id=1, name="Parent1")
        child_no_soft_delete = ChildWithoutSoftDelete(id=1, parent_id=1, name="Child1")

        db_session.add_all([parent, child_no_soft_delete])
        db_session.commit()

        result = BaseRepositoryUtils.soft_delete_cascade_from_parent(
            Parent,
            update_filter="1",
            db=db_session,
        )

        assert result["affected"] == 1

        db_session.expire_all()
        updated_parent = db_session.get(Parent, 1)
        updated_child = db_session.get(ChildWithoutSoftDelete, 1)

        assert updated_parent.deleted_at is not None
        assert updated_child is not None

    @pytest.mark.it("✅  uses custom deleted_at_column parameter")
    def test_uses_custom_deleted_at_column(self, db_session) -> None:
        class CustomParent(Base):
            __tablename__ = "custom_parents"

            id = mapped_column(Integer, primary_key=True)
            name = mapped_column(String(50))
            removed_at = mapped_column(DateTime, nullable=True)

        Base.metadata.create_all(db_session.bind)

        parent = CustomParent(id=1, name="Parent1")
        db_session.add(parent)
        db_session.commit()

        result = BaseRepositoryUtils.soft_delete_cascade_from_parent(
            CustomParent,
            update_filter="1",
            deleted_at_column="removed_at",
            db=db_session,
        )

        assert result["affected"] == 1

        db_session.expire_all()
        updated_parent = db_session.get(CustomParent, 1)
        assert updated_parent.removed_at is not None

    @pytest.mark.it("✅  returns UpdateResult with correct structure")
    def test_returns_correct_update_result_structure(self, db_session) -> None:
        parent = Parent(id=1, name="Parent1")
        child = Child(id=1, parent_id=1, name="Child1")

        db_session.add_all([parent, child])
        db_session.commit()

        result = BaseRepositoryUtils.soft_delete_cascade_from_parent(
            Parent,
            update_filter="1",
            db=db_session,
        )

        assert "raw" in result
        assert "affected" in result
        assert "generated_maps" in result
        assert isinstance(result["raw"], list)
        assert isinstance(result["affected"], int)
        assert isinstance(result["generated_maps"], list)
        assert result["affected"] == 2
        assert len(result["raw"]) == 2
        assert len(result["generated_maps"]) > 0
        assert result["generated_maps"][0] == ["parents", "children"]

    @pytest.mark.it("✅  handles orphan table without mapped class gracefully")
    def test_handles_orphan_table_without_mapped_class(self, db_session) -> None:
        from sqlalchemy import Column, ForeignKeyConstraint, Table

        parent = Parent(id=1, name="Parent1")
        db_session.add(parent)
        db_session.commit()

        Table(
            "orphan_child",
            Base.metadata,
            Column("id", Integer, primary_key=True),
            Column("parent_id", Integer),
            Column("deleted_at", DateTime, nullable=True),
            ForeignKeyConstraint(["parent_id"], ["parents.id"]),
        )
        Base.metadata.create_all(db_session.bind)

        result = BaseRepositoryUtils.soft_delete_cascade_from_parent(
            Parent,
            update_filter="1",
            db=db_session,
        )

        assert result["affected"] == 1
        db_session.expire_all()
        updated_parent = db_session.get(Parent, 1)
        assert updated_parent.deleted_at is not None

    @pytest.mark.it("✅  skips already visited child tables in cascade")
    def test_skips_already_visited_children(self, db_session) -> None:
        class MultiParent1(Base):
            __tablename__ = "multi_parent1"

            id = mapped_column(Integer, primary_key=True)
            name = mapped_column(String(50))
            deleted_at = mapped_column(DateTime, nullable=True)

        class MultiParent2(Base):
            __tablename__ = "multi_parent2"

            id = mapped_column(Integer, primary_key=True)
            multi_parent1_id = mapped_column(Integer, ForeignKey("multi_parent1.id"))
            name = mapped_column(String(50))
            deleted_at = mapped_column(DateTime, nullable=True)

        class SharedChild(Base):
            __tablename__ = "shared_child"

            id = mapped_column(Integer, primary_key=True)
            multi_parent1_id = mapped_column(Integer, ForeignKey("multi_parent1.id"))
            multi_parent2_id = mapped_column(Integer, ForeignKey("multi_parent2.id"))
            name = mapped_column(String(50))
            deleted_at = mapped_column(DateTime, nullable=True)

        Base.metadata.create_all(db_session.bind)

        multi_parent1 = MultiParent1(id=1, name="MultiParent1")
        multi_parent2 = MultiParent2(id=1, multi_parent1_id=1, name="MultiParent2")
        shared_child = SharedChild(id=1, multi_parent1_id=1, multi_parent2_id=1, name="SharedChild")

        db_session.add_all([multi_parent1, multi_parent2, shared_child])
        db_session.commit()

        result = BaseRepositoryUtils.soft_delete_cascade_from_parent(
            MultiParent1,
            update_filter="1",
            db=db_session,
        )

        assert result["affected"] == 3

        db_session.expire_all()
        updated_multi_parent1 = db_session.get(MultiParent1, 1)
        updated_multi_parent2 = db_session.get(MultiParent2, 1)
        updated_shared_child = db_session.get(SharedChild, 1)

        assert updated_multi_parent1.deleted_at is not None
        assert updated_multi_parent2.deleted_at is not None
        assert updated_shared_child.deleted_at is not None
