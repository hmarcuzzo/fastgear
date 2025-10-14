import asyncio
from functools import singledispatchmethod
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from fastgear.common.database.sqlalchemy.repository_utils.inject_db_parameter_decorator import (
    inject_db_parameter_decorator,
    inject_db_parameter_if_missing,
)
from fastgear.common.database.sqlalchemy.session import AllSessionType
from tests.fixtures.common.sqlalchemy_fixtures import mock_db


@pytest.mark.describe("🧪  inject_db_parameter_if_missing")
class TestInjectDbParameterIfMissing:
    @pytest.mark.it("✅  Injects session into async function when missing")
    @pytest.mark.asyncio
    async def test_inject_async_missing(self, mock_db: object):
        @inject_db_parameter_if_missing
        async def sample(db: AllSessionType = None):
            return db

        result = await sample()
        assert result is mock_db

    @pytest.mark.it("✅  Injects session into sync function when missing")
    def test_inject_sync_missing(self, mock_db: object):
        captured: dict[str, Any] = {}

        @inject_db_parameter_if_missing
        def sample(db: AllSessionType = None):
            captured["db"] = db
            return "VALUE"  # Return value intentionally ignored by wrapper for sync funcs

        result = sample()
        assert result == "VALUE"
        assert captured["db"] is mock_db

    @pytest.mark.it("✅  Does not inject when explicit session passed (positional)")
    def test_no_override_positional(self, mock_db: object):
        engine = create_engine("sqlite:///:memory:")
        SessionLocal = sessionmaker(engine, expire_on_commit=False)  # noqa: N806
        real_session: Session = SessionLocal()
        captured: dict[str, Any] = {}

        @inject_db_parameter_if_missing
        def sample(db: AllSessionType = None):
            captured["db"] = db

        sample(real_session)
        assert captured["db"] is real_session

    @pytest.mark.it("✅  Injects when earlier positional args exist")
    def test_inject_with_leading_arg(self, mock_db: object):
        captured: dict[str, Any] = {}

        @inject_db_parameter_if_missing
        def sample(name: str, db: AllSessionType = None):
            captured["db"] = db
            return name

        result = sample("example")
        assert result == "example"
        assert captured["db"] is mock_db

    @pytest.mark.it("✅  Injects when union annotation contains session type")
    def test_union_annotation(self, mock_db: object):
        captured: dict[str, Any] = {}

        @inject_db_parameter_if_missing
        def sample(db: Session | None = None):
            captured["db"] = db

        sample()
        assert captured["db"] is mock_db

    @pytest.mark.it("✅  Injects when no annotation is present")
    def test_no_annotation(self, mock_db: object):
        @inject_db_parameter_if_missing
        def sample(db: AllSessionType):
            return db

        assert sample() == mock_db

    @pytest.mark.it(
        "✅  Does not inject for non-session, non-union annotation (origin branch false)"
    )
    def test_no_injection_for_non_session_annotation(self, mock_db: object):
        captured: dict[str, Any] = {}

        @inject_db_parameter_if_missing
        def sample(db: int = None):  # annotation is plain int; not Union, not session subtype
            captured["db"] = db

        sample()
        # Should remain None because is_valid_session_type returns False when annotation is int
        assert captured["db"] is None

    @pytest.mark.it(
        "✅  Does not inject for non-session union annotation (union branch any() false)"
    )
    def test_no_injection_union_without_session(self, mock_db: object):
        captured: dict[str, Any] = {}

        @inject_db_parameter_if_missing
        def sample(db: int | str | None = None):  # Union contains no session subtype
            captured["db"] = db

        sample()
        assert captured["db"] is None

    @pytest.mark.it("✅  Does not inject when default is non-None (no candidate selected)")
    def test_no_injection_when_default_non_none(self, mock_db: object):
        sentinel = object()

        @inject_db_parameter_if_missing
        def sample(db: AllSessionType = sentinel):
            return db

        assert sample() is sentinel

    @pytest.mark.it(
        "✅  Does not inject when session is provided as keyword arg (needs_injection False)"
    )
    def test_no_injection_when_keyword_session(self, mock_db: object):  # noqa: ARG002
        engine = create_engine("sqlite:///:memory:")
        SessionLocal = sessionmaker(engine, expire_on_commit=False)  # noqa: N806
        real_session: Session = SessionLocal()
        captured: dict[str, Any] = {}

        @inject_db_parameter_if_missing
        def sample(db: AllSessionType = None):
            captured["db"] = db
            return db

        result = sample(db=real_session)
        assert result is real_session
        assert captured["db"] is real_session

    @pytest.mark.it(
        "✅  Does not inject when non-session positional value present at candidate index"
    )
    def test_no_injection_when_positional_non_session_non_none(self, mock_db: object):  # noqa: ARG002
        sentinel = object()
        captured: dict[str, Any] = {}

        @inject_db_parameter_if_missing
        def sample(x: int, db: AllSessionType = None):
            captured["db"] = db
            return x, db

        # Put a non-session, non-None value in the db candidate position
        result = sample(1, sentinel)
        assert result == (1, sentinel)
        assert captured["db"] is sentinel

    @pytest.mark.it("✅  Does not inject when session is provided as keyword arg (awrapper path)")
    @pytest.mark.asyncio
    async def test_async_no_injection_when_keyword_session(self, mock_db: object):  # noqa: ARG002
        engine = create_engine("sqlite:///:memory:")
        SessionLocal = sessionmaker(engine, expire_on_commit=False)  # noqa: N806
        real_session: Session = SessionLocal()

        @inject_db_parameter_if_missing
        async def sample(db: AllSessionType = None):
            return db

        result = await sample(db=real_session)
        assert result is real_session

    @pytest.mark.it(
        "✅  Does not inject when non-session positional value present at candidate index"
    )
    @pytest.mark.asyncio
    async def test_async_no_injection_when_positional_non_session_non_none(
        self,
        mock_db: object,  # noqa: ARG002
    ) -> None:
        sentinel = object()

        @inject_db_parameter_if_missing
        async def sample(x: int, db: AllSessionType = None):
            return x, db

        # Provide a non-session, non-None value at the db parameter position
        result = await sample(1, sentinel)
        assert result == (1, sentinel)

    @pytest.mark.it("✅  Injects when positional arg at candidate index is None")
    def test_positional_none_at_candidate_index_triggers_injection(self, mock_db: object):
        @inject_db_parameter_if_missing
        def sample(*items: Any, db: AllSessionType = None) -> Any:  # db is keyword-only
            return db

        # Two positional args so len(args) > candidate_idx (candidate_idx will be 1)
        # Second positional is None => args[candidate_idx] is None, so line 101 condition is False
        result = sample("x", None)
        assert result is mock_db


@pytest.mark.describe("🧪 inject_db_parameter_decorator (class level)")
class TestInjectDbParameterDecorator:
    @pytest.mark.it("✅  Injects into instance method")
    def test_instance_method(self, mock_db: object):
        container: dict[str, Any] = {}

        @inject_db_parameter_decorator
        class Example:
            def method(self, db: AllSessionType = None):
                container["db"] = db

        ex = Example()
        assert ex.method() is None
        assert container["db"] is mock_db

    @pytest.mark.it("✅  Injects into staticmethod and classmethod")
    def test_static_and_class_methods(self, mock_db: object):
        static_container: dict[str, Any] = {}
        class_container: dict[str, Any] = {}

        @inject_db_parameter_decorator
        class Example:
            @staticmethod
            def static(db: AllSessionType = None):
                static_container["db"] = db

            @classmethod
            def cls(cls, db: AllSessionType = None):
                class_container["db"] = db

        Example.static()
        Example.cls()
        assert static_container["db"] is mock_db
        assert class_container["db"] is mock_db

    @pytest.mark.it("✅  Injects into singledispatchmethod registered implementations")
    def test_singledispatchmethod(self, mock_db: object):
        results: list[Any] = []

        @inject_db_parameter_decorator
        class Example:
            @singledispatchmethod
            def process(self, value: Any, db: AllSessionType = None):
                results.append(("default", db))
                return ("default", db)

            @process.register(int)
            def _(self, value: int, db: AllSessionType = None):
                results.append(("int", db))
                return ("int", db)

        ex = Example()
        int_result = ex.process(5)
        default_result = ex.process("x")

        # Since sync implementations are executed in a thread, wrapper returns None
        assert int_result == ("int", mock_db)
        assert default_result == ("default", mock_db)
        assert ("int", mock_db) in results
        assert ("default", mock_db) in results

    @pytest.mark.it("✅  Does not alter non-callable attributes")
    def test_non_callable_attributes(self):
        @inject_db_parameter_decorator
        class Example:
            value = 42

            def method(self, db: AllSessionType = None):
                return db

        assert Example.value == 42


@pytest.mark.describe("🧪 Concurrency considerations")
class TestConcurrency:
    @pytest.mark.it("✅  Concurrent async calls each see injected session value")
    @pytest.mark.asyncio
    async def test_concurrent_async_calls(self, mock_db: object):
        @inject_db_parameter_if_missing
        async def sample(db: AllSessionType = None):
            await asyncio.sleep(0.01)
            return db

        results = await asyncio.gather(*(sample() for _ in range(5)))
        assert all(r is mock_db for r in results)
