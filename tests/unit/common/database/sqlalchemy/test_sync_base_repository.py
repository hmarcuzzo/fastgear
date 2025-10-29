from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from pydantic import BaseModel
from sqlalchemy import Select, column, delete, table
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

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

    def execute(
        self, stmt: Any, params: Any = None, *, execution_options: dict | None = None
    ) -> _ExecuteResult:
        if not self._execute_queue:
            raise AssertionError("No queued execute() result for statement")
        res = self._execute_queue.pop(0)
        setattr(res, "last_stmt", stmt)
        setattr(res, "last_params", params)
        setattr(res, "last_execution_options", execution_options)
        return res

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

        monkeypatch.setattr(repo.statement_constructor, "build_select_statement", fake_build)
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
            repo.statement_constructor,
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
            repo.statement_constructor,
            "build_options",
            lambda pagination: {"limit": 10, "offset": 0},
        )
        monkeypatch.setattr(
            repo.statement_constructor,
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

        class FakeStmt:
            def returning(self, entity):
                return self

        monkeypatch.setattr(
            repo.statement_constructor,
            "build_update_statement",
            lambda f, payload: FakeStmt(),
        )

        # No change -> empty payload returns early
        result = repo.update("1", {"invalid_field": "value"}, db)
        assert result["affected"] == 0
        assert db.commit_calls == 0

        # With valid change -> affected 1
        updated_user = UserEntity(id="1", name="Bob")
        db.queue_execute(_ExecuteResult(scalars=[updated_user]))

        result = repo.update("1", {"name": "Bob"}, db)
        assert result["affected"] == 1
        assert result["raw"] == [updated_user]
        assert db.commit_calls == 1

    @pytest.mark.it("✅  update accepts Pydantic BaseModel and updates fields accordingly")
    def test_update_with_base_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()

        updated_user = UserEntity(id="3", name="Changed")
        db.queue_execute(_ExecuteResult(scalars=[updated_user]))

        class FakeStmt:
            def returning(self, entity):
                return self

        class UpdateModel(BaseModel):
            name: str

        monkeypatch.setattr(
            repo.statement_constructor,
            "build_update_statement",
            lambda f, payload: FakeStmt(),
        )

        result = repo.update("3", UpdateModel(name="Changed"), db)
        assert result["affected"] == 1
        assert db.commit_calls == 1

    @pytest.mark.it("✅  update with dict payload executes statement and returns result")
    def test_update_with_dict(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()

        updated_user = UserEntity(id="1", name="Updated")
        db.queue_execute(_ExecuteResult(scalars=[updated_user]))

        class FakeStmt:
            def returning(self, entity):
                return self

        called = {}

        def fake_build_update(filter_val, payload):
            called["filter"] = filter_val
            called["payload"] = payload
            return FakeStmt()

        monkeypatch.setattr(
            repo.statement_constructor,
            "build_update_statement",
            fake_build_update,
        )

        result = repo.update("1", {"name": "Updated"}, db)

        assert result["affected"] == 1
        assert result["raw"] == [updated_user]
        assert result["generated_maps"] == []
        assert called["filter"] == "1"
        assert called["payload"] == {"name": "Updated"}
        assert db.flush_calls == 1 or db.commit_calls == 1

    @pytest.mark.it("✅  update with BaseModel converts to dict using model_dump")
    def test_update_with_base_model_conversion(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()

        updated_user = UserEntity(id="2", name="FromModel")
        db.queue_execute(_ExecuteResult(scalars=[updated_user]))

        class FakeStmt:
            def returning(self, entity):
                return self

        called = {}

        def fake_build_update(filter_val, payload):
            called["payload"] = payload
            return FakeStmt()

        monkeypatch.setattr(
            repo.statement_constructor,
            "build_update_statement",
            fake_build_update,
        )

        class UpdateModel(BaseModel):
            name: str
            extra_field: str = "ignored"

        model = UpdateModel(name="FromModel")
        result = repo.update("2", model, db)

        assert result["affected"] == 1
        assert called["payload"] == {"name": "FromModel"}

    @pytest.mark.it("✅  update filters out non-column fields from payload")
    def test_update_filters_non_columns(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()

        updated_user = UserEntity(id="3", name="ValidField")
        db.queue_execute(_ExecuteResult(scalars=[updated_user]))

        class FakeStmt:
            def returning(self, entity):
                return self

        called = {}

        def fake_build_update(filter_val, payload):
            called["payload"] = payload
            return FakeStmt()

        monkeypatch.setattr(
            repo.statement_constructor,
            "build_update_statement",
            fake_build_update,
        )

        payload_with_invalid = {
            "name": "ValidField",
            "invalid_column": "should_be_filtered",
            "another_invalid": 123,
        }

        repo.update("3", payload_with_invalid, db)

        assert called["payload"] == {"name": "ValidField"}
        assert "invalid_column" not in called["payload"]
        assert "another_invalid" not in called["payload"]

    @pytest.mark.it("✅  update returns empty result when payload has no valid columns")
    def test_update_empty_payload(self) -> None:
        repo = UserRepo()
        db = FakeSyncSession()

        result = repo.update("4", {"invalid_field": "value"}, db)

        assert result["affected"] == 0
        assert result["raw"] == []
        assert result["generated_maps"] == []
        assert db.flush_calls == 0
        assert db.commit_calls == 0

    @pytest.mark.it("✅  update returns empty result when payload is empty dict")
    def test_update_completely_empty_payload(self) -> None:
        repo = UserRepo()
        db = FakeSyncSession()

        result = repo.update("5", {}, db)

        assert result["affected"] == 0
        assert result["raw"] == []
        assert result["generated_maps"] == []

    @pytest.mark.it("✅  update prepares cmp_params correctly")
    def test_update_params_preparation(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()

        updated_user = UserEntity(id="6", name="Test")

        class FakeStmt:
            def returning(self, entity):
                return self

        monkeypatch.setattr(
            repo.statement_constructor,
            "build_update_statement",
            lambda f, payload: FakeStmt(),
        )

        execute_params = {}
        original_execute = db.execute

        def capture_execute(stmt, params=None, **kwargs):
            execute_params["captured"] = params
            db.queue_execute(_ExecuteResult(scalars=[updated_user]))
            return original_execute(stmt, params, **kwargs)

        db.execute = capture_execute

        repo.update("6", {"name": "Test", "id": "6"}, db)

        assert "captured" in execute_params
        params = execute_params["captured"]
        assert params["name"] == "Test"
        assert params["id"] == "6"
        assert params["cmp_name"] == "Test"
        assert params["cmp_id"] == "6"

    @pytest.mark.it("✅  update returns multiple affected rows when statement matches multiple")
    def test_update_multiple_rows(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()

        users = [
            UserEntity(id="7", name="Bulk1"),
            UserEntity(id="8", name="Bulk1"),
            UserEntity(id="9", name="Bulk1"),
        ]
        db.queue_execute(_ExecuteResult(scalars=users))

        class FakeStmt:
            def returning(self, entity):
                return self

        monkeypatch.setattr(
            repo.statement_constructor,
            "build_update_statement",
            lambda f, payload: FakeStmt(),
        )

        result = repo.update({"name": "OldName"}, {"name": "Bulk1"}, db)

        assert result["affected"] == 3
        assert len(result["raw"]) == 3
        assert result["raw"] == users

    @pytest.mark.it("✅  update works with UpdateOptions filter")
    def test_update_with_update_options(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()

        updated_user = UserEntity(id="10", name="WithOptions")
        db.queue_execute(_ExecuteResult(scalars=[updated_user]))

        class FakeStmt:
            def returning(self, entity):
                return self

        from fastgear.types.update_options import UpdateOptions

        called = {}

        def fake_build_update(filter_val, payload):
            called["filter"] = filter_val
            return FakeStmt()

        monkeypatch.setattr(
            repo.statement_constructor,
            "build_update_statement",
            fake_build_update,
        )

        options = UpdateOptions(where={"id": "10"})
        result = repo.update(options, {"name": "WithOptions"}, db)

        assert result["affected"] == 1
        assert isinstance(called["filter"], dict)
        assert "where" in called["filter"]
        assert called["filter"]["where"] == {"id": "10"}

    @pytest.mark.it("✅  update calls save after executing statement")
    def test_update_calls_save(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()

        updated_user = UserEntity(id="11", name="SaveTest")
        db.queue_execute(_ExecuteResult(scalars=[updated_user]))

        class FakeStmt:
            def returning(self, entity):
                return self

        monkeypatch.setattr(
            repo.statement_constructor,
            "build_update_statement",
            lambda f, payload: FakeStmt(),
        )

        save_called = {"count": 0}
        original_save = repo.save

        def track_save(db=None):
            save_called["count"] += 1
            return original_save(db)

        monkeypatch.setattr(repo, "save", track_save)

        repo.update("11", {"name": "SaveTest"}, db)

        assert save_called["count"] == 1

    @pytest.mark.it("✅  update with BaseModel exclude_unset works correctly")
    def test_update_base_model_exclude_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()

        updated_user = UserEntity(id="12", name="Partial")
        db.queue_execute(_ExecuteResult(scalars=[updated_user]))

        class FakeStmt:
            def returning(self, entity):
                return self

        called = {}

        def fake_build_update(filter_val, payload):
            called["payload"] = payload
            return FakeStmt()

        monkeypatch.setattr(
            repo.statement_constructor,
            "build_update_statement",
            fake_build_update,
        )

        class UpdateModel(BaseModel):
            name: str | None = None
            id: str | None = None

        model = UpdateModel(name="Partial")
        result = repo.update("12", model, db)

        assert "name" in called["payload"]
        assert "id" not in called["payload"]
        assert result["affected"] == 1

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
            repo.statement_constructor,
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
            lambda entity, update_filter, db: expected,  # noqa: ARG005
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

        def fake_soft_delete(entity, update_filter, db):  # noqa: ARG001
            called["filter"] = update_filter
            return {"raw": [], "affected": 0, "generated_maps": []}

        monkeypatch.setattr(repo.repo_utils, "soft_delete_cascade_from_parent", fake_soft_delete)

        res = repo.soft_delete({"id": "ignored"}, db)
        assert res["affected"] == 0
        assert called["filter"] == {"id": "ignored"}
        assert db.commit_calls == 1

    @pytest.mark.it("✅  soft_delete re-raises exceptions from underlying utility")
    def test_soft_delete_reraises_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()

        # Ensure parent id resolution succeeds without SQLAlchemy inspect
        monkeypatch.setattr(
            repo, "find_one_or_fail", lambda stmt, db=None: UserEntity(id="ANY", name="x")
        )

        def _raise(entity, update_filter, db):  # noqa: ARG001
            raise RuntimeError("boom")

        monkeypatch.setattr(repo.repo_utils, "soft_delete_cascade_from_parent", _raise)

        with pytest.raises(RuntimeError, match="boom"):
            repo.soft_delete("ANY", db)

    @pytest.mark.it("❌  find_one_or_fail converts MultipleResultsFound into NotFoundException")
    def test_find_one_or_fail_multiple_results(self, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = UserRepo()
        db = FakeSyncSession()
        # Ensure build_select_statement returns a bare Select so .limit(2) works
        monkeypatch.setattr(
            repo.statement_constructor,
            "build_select_statement",
            lambda f: Select(),  # noqa: ARG005
        )
        # Queue result that triggers MultipleResultsFound on scalar_one()
        db.queue_execute(_ExecuteResult(one=MultipleResultsFound()))

        with pytest.raises(
            Exception,
            match='Multiple entities of type "UserEntity" found that match with the search filter',
        ):
            repo.find_one_or_fail({"x": 1}, db)
