from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pytest
from pydantic import BaseModel
from sqlalchemy import Select, column, delete, table
from sqlalchemy.exc import NoResultFound

from fastgear.common.database.sqlalchemy.async_base_repository import AsyncBaseRepository
from fastgear.common.database.sqlalchemy.session import db_session
from fastgear.types.pagination import Pagination

if TYPE_CHECKING:
    from collections.abc import Iterable


# ---- Test doubles ----
class _Scalars:
    def __init__(self, items: list[Any] | None = None) -> None:
        self._items = items or []

    def all(self) -> list[Any]:
        return list(self._items)


class _ExecuteResult:
    def __init__(
        self,
        *,
        first: tuple[Any] | None = None,
        one: tuple[Any] | Exception | None = None,
        scalars: list[Any] | None = None,
        count: int | None = None,
        all_rows: list[Any] | None = None,
    ) -> None:
        self._first = first
        self._one = one
        self._scalars = scalars
        self._count = count
        self._all_rows = all_rows

    def first(self) -> tuple[Any] | None:
        return self._first

    def one(self) -> tuple[Any]:
        if isinstance(self._one, Exception):
            raise self._one
        assert self._one is not None
        return self._one

    def scalars(self) -> _Scalars:
        return _Scalars(self._scalars)

    def scalar(self) -> int:
        assert self._count is not None
        return self._count

    # Support Delete branch which expects .all()
    def all(self) -> list[Any]:
        return list(self._all_rows or [])


class FakeAsyncSession:
    def __init__(self) -> None:
        self.added: list[Any] = []
        self.deleted: list[Any] = []
        self.refreshed: list[Any] = []
        self.flush_calls = 0
        self.commit_calls = 0
        self._in_nested = False
        self._execute_queue: list[_ExecuteResult] = []
        self.sync_db = object()

    # configuration helpers
    def queue_execute(self, result: _ExecuteResult) -> None:
        self._execute_queue.append(result)

    # AsyncSession-like API
    def add_all(self, items: Iterable[Any]) -> None:
        self.added.extend(list(items))

    async def flush(self) -> None:
        self.flush_calls += 1

    async def commit(self) -> None:
        self.commit_calls += 1

    def in_nested_transaction(self) -> bool:
        return self._in_nested

    async def refresh(self, entity: Any) -> None:
        self.refreshed.append(entity)

    async def execute(self, stmt: Any) -> _ExecuteResult:
        # Pop next queued result regardless of stmt; tests control ordering
        if not self._execute_queue:
            raise AssertionError("No queued execute() result for statement")
        return self._execute_queue.pop(0)

    async def delete(self, entity: Any) -> None:
        self.deleted.append(entity)

    class _BeginNested:
        def __init__(self, outer: FakeAsyncSession) -> None:
            self._outer = outer

        async def __aenter__(self) -> None:
            self._outer._in_nested = True

        async def __aexit__(self, exc_type, exc, tb) -> None:
            self._outer._in_nested = False

    def begin_nested(self) -> FakeAsyncSession._BeginNested:
        return FakeAsyncSession._BeginNested(self)

    async def run_sync(self, fn):
        # Call provided function with the sync_db stub
        return fn(self.sync_db)


# ---- Sample entity ----
@dataclass
class UserEntity:
    id: str
    name: str


# ---- Concrete repository for tests ----
class UserRepo(AsyncBaseRepository[UserEntity]):
    def __init__(self) -> None:
        super().__init__(UserEntity)


@pytest.mark.describe("🧪  AsyncBaseRepository")
class TestAsyncBaseRepository:
    @pytest.mark.asyncio
    @pytest.mark.it("✅  create_all converts BaseModel/dicts and flushes")
    async def test_create_and_create_all(self) -> None:
        db = FakeAsyncSession()
        repo = UserRepo()

        # prepare a Pydantic BaseModel with model_dump()
        class CreateModel(BaseModel):
            id: str
            name: str

        created = await repo.create_all([CreateModel(id="1", name="alice")], db)
        assert len(created) == 1
        assert isinstance(created[0], UserEntity)
        assert db.flush_calls == 1
        assert db.added
        assert isinstance(db.added[0], UserEntity)

        one = await repo.create(CreateModel(id="2", name="bob"), db)
        assert isinstance(one, UserEntity)

    @pytest.mark.asyncio
    @pytest.mark.it("✅  create_all keeps entity instances as-is (BaseModel branch False)")
    async def test_create_all_with_entity_instance(self) -> None:
        db = FakeAsyncSession()
        repo = UserRepo()
        entity = UserEntity(id="9", name="no-convert")

        created = await repo.create_all([entity], db)
        assert created == [entity]
        assert entity in db.added
        assert db.flush_calls == 1

    @pytest.mark.asyncio
    @pytest.mark.it("✅  save commits or flushes and refreshes when entity provided")
    async def test_save_and_refresh_record(self) -> None:
        db = FakeAsyncSession()
        user = UserEntity(id="u1", name="X")

        # When not in nested transaction -> commit
        await AsyncBaseRepository.commit_or_flush(db)
        assert db.commit_calls == 1
        assert db.flush_calls == 0

        # When in nested transaction -> flush
        async with db.begin_nested():
            await AsyncBaseRepository.commit_or_flush(db)
        assert db.flush_calls == 1

        # refresh_record works for single and list
        db.refreshed.clear()
        await AsyncBaseRepository.refresh_record(user, db)
        await AsyncBaseRepository.refresh_record([user], db)
        assert db.refreshed.count(user) == 2

        # save triggers commit_or_flush + refresh
        db.commit_calls = 0
        db.refreshed.clear()
        result = await AsyncBaseRepository.save(user, db)
        assert result is user
        assert db.commit_calls == 1
        assert user in db.refreshed

    @pytest.mark.asyncio
    @pytest.mark.it("✅  save with None does not refresh (new_record branch False)")
    async def test_save_without_record_does_not_refresh(self) -> None:
        db = FakeAsyncSession()
        db.commit_calls = 0
        db.refreshed.clear()

        result = await AsyncBaseRepository.save(None, db)
        assert result is None
        assert db.commit_calls == 1  # commit still happens
        assert db.refreshed == []  # no refresh when new_record is falsy

    @pytest.mark.asyncio
    @pytest.mark.it("❌  find raises NotImplemented for unsupported types")
    async def test_find_unsupported(self) -> None:
        repo = UserRepo()
        db = FakeAsyncSession()
        with pytest.raises(NotImplementedError):
            await repo.find(object(), db)

    @pytest.mark.asyncio
    @pytest.mark.it("❌  count raises NotImplemented for unsupported types")
    async def test_count_unsupported(self) -> None:
        repo = UserRepo()
        db = FakeAsyncSession()
        with pytest.raises(NotImplementedError):
            await repo.count(object(), db)

    @pytest.mark.asyncio
    @pytest.mark.it("❌  find_and_count raises NotImplemented for unsupported types")
    async def test_find_and_count_unsupported(self) -> None:
        repo = UserRepo()
        db = FakeAsyncSession()
        with pytest.raises(NotImplementedError):
            await repo.find_and_count(object(), db)

    @pytest.mark.asyncio
    @pytest.mark.it("✅  find with Select returns scalars from db.execute")
    async def test_find_with_select(self) -> None:
        repo = UserRepo()
        db = FakeAsyncSession()
        users = [UserEntity(id="1", name="A"), UserEntity(id="2", name="B")]
        db.queue_execute(_ExecuteResult(scalars=users))

        stmt = Select()  # sentinel-like; FakeAsyncSession ignores content
        result = await repo.find(stmt, db)
        assert result == users

    @pytest.mark.asyncio
    @pytest.mark.it("✅  find with options delegates to select constructor then Select overload")
    async def test_find_with_options(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeAsyncSession()
        users = [UserEntity(id="1", name="A")]
        db.queue_execute(_ExecuteResult(scalars=users))

        called: dict[str, Any] = {}

        def fake_build(stmt_or_filter: Any) -> Any:
            called["arg"] = stmt_or_filter
            return Select()

        monkeypatch.setattr(repo.select_constructor, "build_select_statement", fake_build)
        token = db_session.set(db)
        try:
            res = await repo.find({"any": 1}, db)
        finally:
            db_session.reset(token)
        assert res == users
        assert called["arg"] == {"any": 1}

    @pytest.mark.asyncio
    @pytest.mark.it("✅  count with Select returns scalar count from db.execute")
    async def test_count_with_select(self) -> None:
        repo = UserRepo()
        db = FakeAsyncSession()
        db.queue_execute(_ExecuteResult(count=42))

        stmt = Select()
        cnt = await repo.count(stmt, db)
        assert cnt == 42

    @pytest.mark.asyncio
    @pytest.mark.it("✅  count with options delegates to Select overload")
    async def test_count_with_options(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeAsyncSession()
        db.queue_execute(_ExecuteResult(count=5))

        monkeypatch.setattr(
            repo.select_constructor,
            "build_select_statement",
            lambda opts: Select(),
        )
        token = db_session.set(db)
        try:
            cnt = await repo.count({"q": 1}, db)
        finally:
            db_session.reset(token)
        assert cnt == 5

    @pytest.mark.asyncio
    @pytest.mark.it("✅  find_and_count with Pagination delegates and aggregates results")
    async def test_find_and_count_with_pagination(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeAsyncSession()
        # First execute() used by count -> returns scalar
        db.queue_execute(_ExecuteResult(count=2))
        # Second execute() used by find -> returns scalars list
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
        items, total = await repo.find_and_count(pagination, db)
        assert total == 2
        assert len(items) == 2

    @pytest.mark.asyncio
    @pytest.mark.it("✅  update applies only changed fields and persists when needed")
    async def test_update_changed_and_unchanged(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeAsyncSession()

        user = UserEntity(id="1", name="Alice")

        # Provide record via find_one_or_fail
        async def _fake_find_one_or_fail(filt, db=None):
            return user

        monkeypatch.setattr(repo, "find_one_or_fail", _fake_find_one_or_fail)

        # No change -> affected 0, no commit/refresh
        result = await repo.update("1", {"name": "Alice"}, db)
        assert result["affected"] == 0
        assert db.commit_calls == 0
        assert db.refreshed == []

        # Change -> affected 1, commit+refresh
        result = await repo.update("1", {"name": "Bob"}, db)
        assert user.name == "Bob"
        assert result["affected"] == 1
        assert result["raw"] == [user]
        assert db.commit_calls == 1
        assert user in db.refreshed

    @pytest.mark.asyncio
    @pytest.mark.it("✅  update accepts BaseModel and persists when changed")
    async def test_update_with_base_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeAsyncSession()
        user = UserEntity(id="3", name="Start")

        async def _fake_find_one_or_fail(filt, db=None):  # noqa: ANN001
            return user

        class UpdateModel(BaseModel):
            name: str

        monkeypatch.setattr(repo, "find_one_or_fail", _fake_find_one_or_fail)

        result = await repo.update("3", UpdateModel(name="Changed"), db)
        assert user.name == "Changed"
        assert result["affected"] == 1
        assert db.commit_calls == 1
        assert user in db.refreshed

    @pytest.mark.asyncio
    @pytest.mark.it("✅  delete with Delete statement executes and commits")
    async def test_delete_with_delete_statement(self) -> None:
        repo = UserRepo()
        db = FakeAsyncSession()
        # Prepare a dummy table and Delete statement
        t = table("t", column("id"))
        stmt = delete(t).where(t.c.id == "x")

        # Queue an execute result that supports .all()
        db.queue_execute(_ExecuteResult(all_rows=[("row",)]))

        res = await repo.delete(stmt, db)
        assert res["affected"] == 1
        assert res["raw"] == [("row",)]
        assert db.commit_calls == 1

    @pytest.mark.asyncio
    @pytest.mark.it("✅  delete with id deletes entity and commits")
    async def test_delete_with_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeAsyncSession()

        # Use non-Delete branch: resolve record by id via find_one_or_fail
        user = UserEntity(id="del1", name="Z")

        async def _fake_find_one_or_fail(stmt, db=None):
            return user

        monkeypatch.setattr(repo, "find_one_or_fail", _fake_find_one_or_fail)

        res = await repo.delete("del1", db)
        assert res["raw"] == ["del1"]
        assert res["affected"] == 1
        assert user in db.deleted
        assert db.commit_calls == 1

    @pytest.mark.asyncio
    @pytest.mark.it("✅  find_one and find_one_or_fail use select_constructor and db.execute")
    async def test_find_one_variants(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeAsyncSession()
        # find_one -> first() returns None
        db.queue_execute(_ExecuteResult(first=None))
        monkeypatch.setattr(
            repo.select_constructor,
            "build_select_statement",
            lambda f: Select(),
        )
        res = await repo.find_one({"x": 1}, db)
        assert res is None

        # find_one -> first() returns (entity,)
        db.queue_execute(_ExecuteResult(first=(UserEntity(id="1", name="A"),)))
        res2 = await repo.find_one({"y": 2}, db)
        assert isinstance(res2, UserEntity)

        # find_one_or_fail -> .one() raises NoResultFound
        db.queue_execute(_ExecuteResult(one=NoResultFound()))
        with pytest.raises(
            Exception,
            match='Could not find any entity of type "UserEntity" that matches with the search filter',
        ):
            await repo.find_one_or_fail("filter", db)

        # find_one_or_fail -> .one() returns entity
        db.queue_execute(_ExecuteResult(one=(UserEntity(id="2", name="B"),)))
        got = await repo.find_one_or_fail("filter", db)
        assert got.id == "2"

    @pytest.mark.asyncio
    @pytest.mark.it("✅  soft_delete uses run_sync and commits, with string id")
    async def test_soft_delete_with_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeAsyncSession()

        # Stub repo_utils to return a known response
        expected = {"raw": ["ok"], "affected": 3, "generated_maps": [["a", "b"]]}
        monkeypatch.setattr(
            repo.repo_utils,
            "soft_delete_cascade_from_parent",
            lambda entity, parent_entity_id, db=None: expected,
        )

        res = await repo.soft_delete("U1", db)
        assert res == expected
        # commit_or_flush called after nested tx -> commit
        assert db.commit_calls == 1

    @pytest.mark.asyncio
    @pytest.mark.it("✅  soft_delete with filter resolves record id then calls run_sync")
    async def test_soft_delete_with_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeAsyncSession()

        user = UserEntity(id="ID-7", name="T")

        async def _fake_find_one_or_fail(f, db=None):
            return user

        monkeypatch.setattr(repo, "find_one_or_fail", _fake_find_one_or_fail)

        called: dict[str, Any] = {}

        def fake_soft_delete(entity, parent_entity_id, db=None):  # noqa: ANN001, ARG001
            called["id"] = parent_entity_id
            return {"raw": [], "affected": 0, "generated_maps": []}

        monkeypatch.setattr(repo.repo_utils, "soft_delete_cascade_from_parent", fake_soft_delete)

        res = await repo.soft_delete({"id": "ignored"}, db)
        assert res["affected"] == 0
        assert called["id"] == "ID-7"
        assert db.commit_calls == 1

    @pytest.mark.asyncio
    @pytest.mark.it("❌  soft_delete re-raises inner exception")
    async def test_soft_delete_reraises_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeAsyncSession()

        # Cause the inner function executed in run_sync to raise
        def _raise(entity, parent_entity_id, db=None):  # noqa: ANN001, ARG001
            raise RuntimeError("boom")

        monkeypatch.setattr(repo.repo_utils, "soft_delete_cascade_from_parent", _raise)

        with pytest.raises(RuntimeError, match="boom"):
            await repo.soft_delete("ANY", db)
