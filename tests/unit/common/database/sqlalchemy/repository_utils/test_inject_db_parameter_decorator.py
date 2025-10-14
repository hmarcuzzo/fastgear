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
    async def test_inject_async_missing(self, mock_db: Any):
        @inject_db_parameter_if_missing
        async def sample(db: AllSessionType = None):
            return db

        result = await sample()
        assert result is mock_db

    @pytest.mark.it("✅  Injects session into sync function when missing and discards return")
    @pytest.mark.asyncio
    async def test_inject_sync_missing(self, mock_db: Any):
        captured: dict[str, Any] = {}

        @inject_db_parameter_if_missing
        def sample(db: AllSessionType = None):
            captured["db"] = db
            return "VALUE"  # Return value intentionally ignored by wrapper for sync funcs

        result = await sample()
        assert result is None  # Wrapper returns None for sync functions
        assert captured["db"] is mock_db

    @pytest.mark.it("✅  Does not inject when explicit session passed (positional)")
    @pytest.mark.asyncio
    async def test_no_override_positional(self, mock_db: Any):
        engine = create_engine("sqlite:///:memory:")
        SessionLocal = sessionmaker(engine, expire_on_commit=False)  # noqa: N806
        real_session: Session = SessionLocal()
        captured: dict[str, Any] = {}

        @inject_db_parameter_if_missing
        def sample(db: AllSessionType = None):
            captured["db"] = db

        await sample(real_session)
        assert captured["db"] is real_session

    @pytest.mark.it("✅  Injects when earlier positional args exist")
    @pytest.mark.asyncio
    async def test_inject_with_leading_arg(self, mock_db: Any):
        captured: dict[str, Any] = {}

        @inject_db_parameter_if_missing
        def sample(name: str, db: AllSessionType = None):
            captured["db"] = db
            return name

        result = await sample("example")
        assert result is None  # sync wrapper returns None
        assert captured["db"] is mock_db

    @pytest.mark.it("✅  Injects when union annotation contains session type")
    @pytest.mark.asyncio
    async def test_union_annotation(self, mock_db: Any):
        captured: dict[str, Any] = {}

        @inject_db_parameter_if_missing
        def sample(db: Session | None = None):
            captured["db"] = db

        await sample()
        assert captured["db"] is mock_db

    @pytest.mark.it("✅  Does not inject when parameter has no default (current behavior)")
    @pytest.mark.asyncio
    async def test_no_default_not_injected(self, mock_db: Any):
        @inject_db_parameter_if_missing
        def sample(db: AllSessionType):
            return db

        with pytest.raises(TypeError):
            await sample()  # Missing required positional argument

    @pytest.mark.it(
        "✅  Does not inject for non-session, non-union annotation (origin branch false)"
    )
    @pytest.mark.asyncio
    async def test_no_injection_for_non_session_annotation(self, mock_db: Any):
        captured: dict[str, Any] = {}

        @inject_db_parameter_if_missing
        def sample(db: int = None):  # annotation is plain int; not Union, not session subtype
            captured["db"] = db

        await sample()
        # Should remain None because is_valid_session_type returns False when annotation is int
        assert captured["db"] is None

    @pytest.mark.it(
        "✅  Does not inject for non-session union annotation (union branch any() false)"
    )
    @pytest.mark.asyncio
    async def test_no_injection_union_without_session(self, mock_db: Any):
        captured: dict[str, Any] = {}

        @inject_db_parameter_if_missing
        def sample(db: int | str | None = None):  # Union contains no session subtype
            captured["db"] = db

        await sample()
        assert captured["db"] is None


@pytest.mark.describe("🧪 inject_db_parameter_decorator (class level)")
class TestInjectDbParameterDecorator:
    @pytest.mark.it("✅  Injects into instance method")
    @pytest.mark.asyncio
    async def test_instance_method(self, mock_db: Any):
        container: dict[str, Any] = {}

        @inject_db_parameter_decorator
        class Example:
            def method(self, db: AllSessionType = None):
                container["db"] = db

        ex = Example()
        result = await ex.method()
        assert result is None
        assert container["db"] is mock_db

    @pytest.mark.it("✅  Injects into staticmethod and classmethod")
    @pytest.mark.asyncio
    async def test_static_and_class_methods(self, mock_db: Any):
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

        await Example.static()
        await Example.cls()
        assert static_container["db"] is mock_db
        assert class_container["db"] is mock_db

    @pytest.mark.it("✅  Injects into singledispatchmethod registered implementations")
    @pytest.mark.asyncio
    async def test_singledispatchmethod(self, mock_db: Any):
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
        int_result = await ex.process(5)
        default_result = await ex.process("x")

        # Since sync implementations are executed in a thread, wrapper returns None
        assert int_result is None
        assert default_result is None
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
    async def test_concurrent_async_calls(self, mock_db: Any):
        @inject_db_parameter_if_missing
        async def sample(db: AllSessionType = None):
            await asyncio.sleep(0.01)
            return db

        results = await asyncio.gather(*(sample() for _ in range(5)))
        assert all(r is mock_db for r in results)
