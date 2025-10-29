from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import ForeignKey, Integer
from sqlalchemy import String as SAString
from sqlalchemy.dialects import sqlite
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from fastgear.common.database.sqlalchemy.repository_utils.statement_constructor import (
    StatementConstructor,
)
from fastgear.types.pagination import Pagination


class Base(DeclarativeBase):
    pass


class Parent(Base):  # type: ignore[valid-type]
    __tablename__ = "parent_sc"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(SAString, nullable=False)
    children: Mapped[list[Child]] = relationship(back_populates="parent")  # type: ignore[name-defined]


class Child(Base):  # type: ignore[valid-type]
    __tablename__ = "child_sc"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("parent_sc.id"), nullable=False)
    parent: Mapped[Parent] = relationship(back_populates="children")


def _sql(stmt: Any) -> str:
    return str(stmt.compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True}))


@pytest.mark.describe("🧪  StatementConstructor")
class TestStatementConstructor:
    @pytest.mark.it("✅  build_select_statement with string criteria filters by primary key")
    def test_build_select_with_string_pk(self) -> None:
        sc = StatementConstructor(Parent)
        stmt = sc.build_select_statement("1")
        sql = _sql(stmt)
        # Should select from parent_sc and include a WHERE on id
        assert "FROM parent_sc" in sql
        assert "WHERE" in sql
        assert "parent_sc.id =" in sql

    @pytest.mark.it("✅  applies options: where/order_by/skip/take/relations/select/with_deleted")
    def test_apply_various_options(self) -> None:
        sc = StatementConstructor(Parent)
        # Single where expression (not list) to exercise __fix_options_dict
        options: dict[str, Any] = {
            "where": Parent.name == "A",
            "order_by": [Parent.id.desc()],
            "skip": 5,
            "take": 10,
            "relations": ["children"],
            "select": [Parent.name],
            "with_deleted": True,
        }
        stmt = sc.build_select_statement(options)
        sql = _sql(stmt)
        assert "ORDER BY parent_sc.id DESC" in sql
        assert " LIMIT 10" in sql
        assert " OFFSET 5" in sql
        # Execution option set
        assert stmt.get_execution_options().get("with_deleted") is True

    @pytest.mark.it("❌ unknown option key raises KeyError")
    def test_unknown_option_raises(self) -> None:
        sc = StatementConstructor(Parent)
        with pytest.raises(KeyError, match="Unknown option: bad in FindOptions"):
            sc.build_select_statement({"bad": 1})  # type: ignore[arg-type]

    @pytest.mark.it("✅  build_options from Pagination maps search/sort/columns correctly")
    def test_build_options_from_pagination(self) -> None:
        sc = StatementConstructor(Parent)
        # Two search groups: single and OR of two
        pagination = Pagination(
            skip=2,
            take=10,
            sort=[{"field": "name", "by": "ASC"}, {"field": "id", "by": "DESC"}],
            search=[
                {"field": "name", "value": "X"},
                [{"field": "name", "value": "Y"}, {"field": "name", "value": "Z"}],
            ],
            columns=["children", "name", "unknown_field"],
        )
        opts = sc.build_options(pagination)

        # skip is converted in Pagination.__post_init__ to (skip-1)*take => (2-1)*take = 10
        assert opts["skip"] == 10
        assert opts["take"] == 10

        where = opts["where"]
        assert len(where) == 2
        # The second clause should combine with OR
        assert " OR " in str(where[1])

        order_by = opts["order_by"]
        assert len(order_by) == 2
        assert "ASC" in str(order_by[0])
        assert "DESC" in str(order_by[1])

        # Relationship recognized, scalar column added to select, unknown kept as-is
        assert "children" in opts["relations"]
        # SQLAlchemy may render attributes differently across versions; check attribute key
        assert any(getattr(sel, "key", None) == "name" for sel in opts["select"])
        assert any(item == "unknown_field" for item in opts["select"])

    @pytest.mark.it("✅  build_select_statement with no options returns plain select")
    def test_build_select_without_options_returns_plain_select(self) -> None:
        sc = StatementConstructor(Parent)
        # criteria None -> options_dict falsy -> early return branch
        stmt = sc.build_select_statement(None)
        sql = _sql(stmt)
        assert "FROM parent_sc" in sql
        assert "WHERE" not in sql
        assert "ORDER BY" not in sql
        assert " LIMIT " not in sql
        assert " OFFSET " not in sql

    @pytest.mark.it("✅  build_options puts relationship fields into relations list")
    def test_build_options_relations_branch(self) -> None:
        sc = StatementConstructor(Parent)
        pagination = Pagination(
            skip=1,
            take=5,
            sort=[],
            search=[],
            columns=["children"],  # only relationship field
        )
        opts = sc.build_options(pagination)
        assert opts["relations"] == ["children"]
        assert opts["select"] == []

    @pytest.mark.it("✅  build_options skips empty search groups (if not clauses)")
    def test_build_options_skips_empty_search_groups(self) -> None:
        sc = StatementConstructor(Parent)
        pagination = Pagination(
            skip=1,
            take=5,
            sort=[],
            search=[[], {"field": "name", "value": "A"}],  # first group empty -> skipped
            columns=[],
        )
        opts = sc.build_options(pagination)
        where = opts["where"]
        # Only the non-empty group should yield a clause
        assert len(where) == 1
        assert "name" in str(where[0])

    @pytest.mark.it("✅  extract_from_mapping flattens list values and preserves scalars/defaults")
    def test_extract_from_mapping_mixed(self) -> None:
        mapping = {"a": ["x", "y"], "b": "z"}
        fields = ["a", "b", "c"]  # 'c' not in mapping -> falls back to field itself
        result = StatementConstructor.extract_from_mapping(mapping, fields)
        assert result == ["x", "y", "z", "c"]

    @pytest.mark.it("✅  build_update_statement with UpdateOptions filters by where clause")
    def test_build_update_with_update_options(self) -> None:
        sc = StatementConstructor(Parent)
        payload = {"name": "Updated"}
        options = {"where": [Parent.id == 1]}
        stmt = sc.build_update_statement(options, payload=payload)
        sql = _sql(stmt)
        assert "UPDATE parent_sc" in sql
        assert "WHERE" in sql
        assert "parent_sc.id =" in sql
        assert "parent_sc.name IS NOT ?" in sql

    @pytest.mark.it("✅  build_update_statement with string criteria filters by primary key")
    def test_build_update_with_string_pk(self) -> None:
        sc = StatementConstructor(Parent)
        payload = {"name": "Updated"}
        stmt = sc.build_update_statement("1", payload=payload)
        sql = _sql(stmt)
        assert "UPDATE parent_sc" in sql
        assert "WHERE" in sql
        assert "parent_sc.id =" in sql
        assert "parent_sc.name IS NOT ?" in sql

    @pytest.mark.it("✅  build_update_statement adds distinct_from conditions for payload fields")
    def test_build_update_adds_distinct_from_conditions(self) -> None:
        sc = StatementConstructor(Parent)
        payload = {"name": "NewName", "id": 5}
        options = {"where": [Parent.id > 0]}
        stmt = sc.build_update_statement(options, payload=payload)
        sql = _sql(stmt)
        assert " OR " in sql
        assert sql.count("IS NOT ?") >= 2

    @pytest.mark.it("✅  build_update_statement with new_entity uses provided entity")
    def test_build_update_with_new_entity(self) -> None:
        sc = StatementConstructor(Parent)
        payload = {"parent_id": 2}
        options = {"where": [Child.id == 1]}
        stmt = sc.build_update_statement(options, new_entity=Child, payload=payload)
        sql = _sql(stmt)
        assert "UPDATE child_sc" in sql
        assert "child_sc.id =" in sql
        assert "child_sc.parent_id IS NOT ?" in sql

    @pytest.mark.it("❌  build_update_statement with unknown option raises KeyError")
    def test_build_update_with_unknown_option_raises(self) -> None:
        sc = StatementConstructor(Parent)
        payload = {"name": "Updated"}
        options = {"where": [Parent.id == 1], "bad": "option"}  # type: ignore[dict-item]
        with pytest.raises(KeyError, match="Unknown option: bad in UpdateOptions"):
            sc.build_update_statement(options, payload=payload)
