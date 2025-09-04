from typing import Any

import pytest
from fastapi import FastAPI

from fastgear import applications
from tests.fixtures.api import app


@pytest.mark.describe("🧪  Applications")
class TestApplications:
    @pytest.mark.it("✅  Should call all registered utility callables with the correct parameters")
    def test_apply_utils_calls_registered_utils(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[tuple[str, dict]] = []

        def make_callable(name: str):
            def _call(a: FastAPI, **kwargs: Any) -> None:
                # ensure the same app instance is forwarded
                assert a is app
                calls.append((name, kwargs))

            return _call

        monkeypatch.setattr(
            applications,
            "UTILS_CALLABLES",
            {"first": make_callable("first"), "second": make_callable("second")},
        )

        applications.apply_utils(app, ["first", "second"], option=123)

        assert calls == [("first", {"option": 123}), ("second", {"option": 123})]

    @pytest.mark.it("✅  Should suppress unknown utility names without raising errors")
    def test_apply_utils_suppresses_unknown_utils(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[str] = []

        monkeypatch.setattr(
            applications, "UTILS_CALLABLES", {"exists": lambda a, **kwargs: calls.append("exists")}
        )

        # 'missing' key does not exist in UTILS_CALLABLES; apply_utils should suppress it
        applications.apply_utils(app, ["exists", "missing"])

        assert calls == ["exists"]

    @pytest.mark.it("✅  Should forward keyword arguments to the utility callables")
    def test_apply_utils_forwards_kwargs_to_callable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        received: dict[str, Any] = {}

        def recorder(a: FastAPI, **kwargs: Any) -> None:
            received.update(kwargs)

        monkeypatch.setattr(applications, "UTILS_CALLABLES", {"rec": recorder})

        applications.apply_utils(app, ["rec"], alpha=1, beta="x")

        assert received == {"alpha": 1, "beta": "x"}
