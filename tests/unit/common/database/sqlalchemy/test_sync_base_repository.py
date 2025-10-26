from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from pydantic import BaseModel
from sqlalchemy import Select, column, delete, table
from sqlalchemy.exc import NoResultFound

from fastgear.common.database.sqlalchemy.sync_base_repository import SyncBaseRepository
from fastgear.types.pagination import Pagination
from tests.fixtures.common.base_repository_fixtures import UserEntity, _ExecuteResult

if TYPE_CHECKING:
    from collections.abc import Iterable


class FakeSyncSession:
    def __init__(self) -> None:
        self.added: list[Any] = []
        self.deleted: list[Any] = []
        self.refreshed: list[Any] = []
        self.flush_calls = 0
        self.commit_calls = 0
        self._in_nested = False
        self._execute_queue: list[_ExecuteResult] = []

    # configuration helpers
    def queue_execute(self, result: _ExecuteResult) -> None:
        self._execute_queue.append(result)

    # Session-like API
    def add_all(self, items: Iterable[Any]) -> None:
        self.added.extend(list(items))

    def flush(self) -> None:
        self.flush_calls += 1

    def commit(self) -> None:
        self.commit_calls += 1

    def in_nested_transaction(self) -> bool:
        return self._in_nested

    def refresh(self, entity: Any) -> None:
        self.refreshed.append(entity)

    def execute(self, stmt: Any) -> _ExecuteResult:
        if not self._execute_queue:
            raise AssertionError("No queued execute() result for statement")
        return self._execute_queue.pop(0)

    def scalar(self, stmt: Any) -> Any:
        # Mirror SyncSession.scalar() by returning a scalar value from queued results
        if not self._execute_queue:
            raise AssertionError("No queued scalar() result for statement")
        return self._execute_queue.pop(0).scalar()

    def delete(self, entity: Any) -> None:
        self.deleted.append(entity)

    class _BeginNested:
        def __init__(self, outer: FakeSyncSession) -> None:
            self._outer = outer

        def __enter__(self) -> None:
            self._outer._in_nested = True

        def __exit__(self, exc_type, exc, tb) -> None:
            self._outer._in_nested = False

    def begin_nested(self) -> FakeSyncSession._BeginNested:
        return FakeSyncSession._BeginNested(self)


# ---- Concrete repository for tests ----
class UserRepo(SyncBaseRepository[UserEntity]):
    def __init__(self) -> None:
        super().__init__(UserEntity)


@pytest.mark.describe("🧪  SyncBaseRepository")
class TestSyncBaseRepository:
    @pytest.mark.it("✅  create_all converts and creates entities, create creates one entity")
    def test_create_and_create_all(self) -> None:
        db = FakeSyncSession()
        repo = UserRepo()

        class CreateModel(BaseModel):
            id: str
            name: str

        created = repo.create_all([CreateModel(id="1", name="alice")], db)
        assert len(created) == 1
        assert isinstance(created[0], UserEntity)
        assert db.flush_calls == 1
        assert db.added
        assert isinstance(db.added[0], UserEntity)

        one = repo.create(CreateModel(id="2", name="bob"), db)
        assert isinstance(one, UserEntity)

    @pytest.mark.it("✅  create_all accepts entity instances without conversion")
    def test_create_all_with_entity_instance(self) -> None:
        db = FakeSyncSession()
        repo = UserRepo()
        entity = UserEntity(id="9", name="no-convert")

        created = repo.create_all([entity], db)
        assert created == [entity]
        assert entity in db.added
        assert db.flush_calls == 1

    @pytest.mark.it("✅  save(None) commits but does not refresh anything")
    def test_save_without_record_does_not_refresh(self) -> None:
        db = FakeSyncSession()
        db.commit_calls = 0
        db.refreshed.clear()

        result = SyncBaseRepository.save(db)
        assert result is None
        assert db.commit_calls == 1
        assert db.refreshed == []

    @pytest.mark.it("✅  find raises NotImplementedError for unsupported input")
    def test_find_unsupported(self) -> None:
        repo = UserRepo()
        db = FakeSyncSession()
        with pytest.raises(NotImplementedError):
            repo.find(object(), db)

    @pytest.mark.it("✅  count raises NotImplementedError for unsupported input")
    def test_find_with_select(self) -> None:
        repo = UserRepo()
        db = FakeSyncSession()
        users = [UserEntity(id="1", name="A"), UserEntity(id="2", name="B")]
        db.queue_execute(_ExecuteResult(scalars=users))

        stmt = Select()
        result = repo.find(stmt, db)
        assert result == users

    @pytest.mark.it("✅  find constructs select statement from options")
    def test_find_with_options(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()
        users = [UserEntity(id="1", name="A")]
        db.queue_execute(_ExecuteResult(scalars=users))

        called: dict[str, Any] = {}

        def fake_build(stmt_or_filter: Any) -> Any:
            called["arg"] = stmt_or_filter
            return Select()

        monkeypatch.setattr(repo.select_constructor, "build_select_statement", fake_build)
        res = repo.find({"any": 1}, db)
        assert res == users
        assert called["arg"] == {"any": 1}

    @pytest.mark.asyncio
    @pytest.mark.it("❌  find raises NotImplemented for unsupported types")
    async def test_find_unsupported(self) -> None:
        repo = UserRepo()
        db = FakeSyncSession()
        with pytest.raises(NotImplementedError):
            repo.find(object(), db)

    @pytest.mark.asyncio
    @pytest.mark.it("❌  count raises NotImplemented for unsupported types")
    async def test_count_unsupported(self) -> None:
        repo = UserRepo()
        db = FakeSyncSession()
        with pytest.raises(NotImplementedError):
            repo.count(object(), db)

    @pytest.mark.it("✅  count with Select statement returns correct count")
    def test_count_with_select(self) -> None:
        repo = UserRepo()
        db = FakeSyncSession()
        db.queue_execute(_ExecuteResult(count=42))

        stmt = Select()
        cnt = repo.count(stmt, db)
        assert cnt == 42

    @pytest.mark.it("✅  count constructs select statement from options")
    def test_count_with_options(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()
        db.queue_execute(_ExecuteResult(count=5))

        monkeypatch.setattr(
            repo.select_constructor,
            "build_select_statement",
            lambda opts: Select(),
        )
        cnt = repo.count({"q": 1}, db)
        assert cnt == 5

    @pytest.mark.it("✅  find_and_count with pagination returns correct items and total")
    def test_find_and_count_with_pagination(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()
        db.queue_execute(_ExecuteResult(count=2))
        db.queue_execute(
            _ExecuteResult(scalars=[UserEntity(id="1", name="A"), UserEntity(id="2", name="B")])
        )

        monkeypatch.setattr(
            repo.select_constructor,
            "build_options",
            lambda pagination: {"limit": 10, "offset": 0},
        )
        monkeypatch.setattr(
            repo.select_constructor,
            "build_select_statement",
            lambda opts: Select(),
        )

        pagination = Pagination(skip=1, take=10, sort=[], search=[], columns=[])
        # Sync repo registers async implementations for find_and_count, so run the coroutine
        items, total = repo.find_and_count(pagination, db)
        assert total == 2
        assert len(items) == 2

    @pytest.mark.asyncio
    @pytest.mark.it("❌  find_and_count raises NotImplemented for unsupported types")
    async def test_find_and_count_unsupported(self) -> None:
        repo = UserRepo()
        db = FakeSyncSession()
        with pytest.raises(NotImplementedError):
            repo.find_and_count(object(), db)

    @pytest.mark.it("✅  update updates changed fields and skips unchanged fields")
    def test_update_changed_and_unchanged(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()

        user = UserEntity(id="1", name="Alice")

        def _fake_find_one_or_fail(filt, db=None):
            return user

        monkeypatch.setattr(repo, "find_one_or_fail", _fake_find_one_or_fail)

        result = repo.update("1", {"name": "Alice"}, db)
        assert result["affected"] == 0
        assert db.commit_calls == 0

        result = repo.update("1", {"name": "Bob"}, db)
        assert user.name == "Bob"
        assert result["affected"] == 1
        assert result["raw"] == [user]
        assert db.commit_calls == 1

    @pytest.mark.it("✅  update accepts Pydantic BaseModel and updates fields accordingly")
    def test_update_with_base_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()
        user = UserEntity(id="3", name="Start")

        def _fake_find_one_or_fail(filt, db=None):
            return user

        class UpdateModel(BaseModel):
            name: str

        monkeypatch.setattr(repo, "find_one_or_fail", _fake_find_one_or_fail)

        result = repo.update("3", UpdateModel(name="Changed"), db)
        assert user.name == "Changed"
        assert result["affected"] == 1
        assert db.commit_calls == 1

    @pytest.mark.it("✅  delete with Delete statement executes deletion correctly")
    def test_delete_with_delete_statement(self) -> None:
        repo = UserRepo()
        db = FakeSyncSession()
        t = table("t", column("id"))
        stmt = delete(t).where(t.c.id == "x")

        db.queue_execute(_ExecuteResult(all_rows=[("row",)]))

        res = repo.delete(stmt, db)
        assert res["affected"] == 1
        assert res["raw"] == [("row",)]
        assert db.commit_calls == 1

    @pytest.mark.it("✅  delete with id deletes the correct entity")
    def test_delete_with_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()
        user = UserEntity(id="del1", name="Z")

        def _fake_find_one_or_fail(stmt, db=None):
            return user

        monkeypatch.setattr(repo, "find_one_or_fail", _fake_find_one_or_fail)

        res = repo.delete("del1", db)
        assert res["raw"] == ["del1"]
        assert res["affected"] == 1
        assert user in db.deleted
        assert db.commit_calls == 1

    @pytest.mark.it("✅  find_one and find_one_or_fail behave correctly")
    def test_find_one_variants(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()
        db.queue_execute(_ExecuteResult(first=None))
        monkeypatch.setattr(
            repo.select_constructor,
            "build_select_statement",
            lambda f: Select(),
        )
        res = repo.find_one({"x": 1}, db)
        assert res is None

        db.queue_execute(_ExecuteResult(first=(UserEntity(id="1", name="A"),)))
        res2 = repo.find_one({"y": 2}, db)
        assert isinstance(res2, UserEntity)

        db.queue_execute(_ExecuteResult(one=NoResultFound()))
        with pytest.raises(
            Exception,
            match='Could not find any entity of type "UserEntity" that matches with the search filter',
        ):
            repo.find_one_or_fail("filter", db)

        db.queue_execute(_ExecuteResult(one=(UserEntity(id="2", name="B"),)))
        got = repo.find_one_or_fail("filter", db)
        assert got.id == "2"

    @pytest.mark.it("✅  soft_delete with id or filter behaves correctly")
    def test_soft_delete_with_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()

        # Avoid select_constructor.inspect by returning a known entity directly
        monkeypatch.setattr(
            repo,
            "find_one_or_fail",
            lambda stmt, db=None: UserEntity(id="U1", name="stub"),  # noqa: ARG001
        )

        expected = {"raw": ["ok"], "affected": 3, "generated_maps": [["a", "b"]]}
        monkeypatch.setattr(
            repo.repo_utils,
            "soft_delete_cascade_from_parent",
            lambda entity, parent_entity_id, db=None: expected,
        )

        res = repo.soft_delete("U1", db)
        assert res == expected
        assert db.commit_calls == 1

    @pytest.mark.it("✅  soft_delete with filter behaves correctly")
    def test_soft_delete_with_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()

        user = UserEntity(id="ID-7", name="T")

        def _fake_find_one_or_fail(f, db=None):
            return user

        monkeypatch.setattr(repo, "find_one_or_fail", _fake_find_one_or_fail)

        called: dict[str, Any] = {}

        def fake_soft_delete(entity, parent_entity_id, db=None):
            called["id"] = parent_entity_id
            return {"raw": [], "affected": 0, "generated_maps": []}

        monkeypatch.setattr(repo.repo_utils, "soft_delete_cascade_from_parent", fake_soft_delete)

        res = repo.soft_delete({"id": "ignored"}, db)
        assert res["affected"] == 0
        assert called["id"] == "ID-7"
        assert db.commit_calls == 1

    @pytest.mark.it("✅  soft_delete re-raises exceptions from underlying utility")
    def test_soft_delete_reraises_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()

        # Ensure parent id resolution succeeds without SQLAlchemy inspect
        monkeypatch.setattr(
            repo, "find_one_or_fail", lambda stmt, db=None: UserEntity(id="ANY", name="x")
        )

        def _raise(entity, parent_entity_id, db=None):
            raise RuntimeError("boom")

        monkeypatch.setattr(repo.repo_utils, "soft_delete_cascade_from_parent", _raise)

        with pytest.raises(RuntimeError, match="boom"):
            repo.soft_delete("ANY", db)
