---
paths:
  - "tests/**/*.py"
---

# Tests

`uv run pytest` runs the whole suite. `addopts` already turns on branch coverage over `fastgear`
and the testdox reporter, so the run reads as a sentence per test — which is why every test
carries the markers below.

## Layout

`tests/unit/` mirrors `fastgear/` all the way down, one test module per source module:
`utils/pagination_utils.py` is covered by `tests/unit/utils/test_pagination_utils.py`. Every
package on the way needs an `__init__.py`.

`tests/fixtures/` mirrors the same tree and holds nothing but fixtures and the doubles they
build: `tests/fixtures/types/pagination_fixtures.py`, `tests/fixtures/common/sqlalchemy_fixtures.py`.
A test module imports the fixtures it uses by name; `F401` is ignored under `tests/` because
pytest resolves them by name and the import looks unused.

`tests/conftest.py` carries only what the whole suite shares — the `AsyncClient` over
`tests/fixtures/api`'s app, and `anyio_backend`.

The suite covers a library whose SQLAlchemy and Redis support is optional, so a test that needs
an extra belongs in the directory mirroring that module and nowhere else; CI installs the extras
with `uv sync --all-extras --group test`.

## Structure

Plain classes named after the subject under test, `TestJsonUtils`, never `unittest.TestCase`,
which would break fixtures, `monkeypatch` and `parametrize`. Keep no mutable state on the class
body: pytest builds a new instance per test, so a shared attribute only looks isolated until
something mutates it.

The class carries the subject, so the method names carry only the behaviour: inside
`TestCustomEnumBehavior`, `test_object_name_from_instance` is enough.

Each class declares the subject and each test declares its behaviour, in the project's testdox
style — two spaces after the emoji, `✅` for the expected path and `❌` for a failure:

```python
@pytest.mark.describe("🧪  JsonUtils")
class TestJsonUtils:
    @pytest.mark.it("✅  Should serialize datetime objects to ISO format")
    def test_json_serial_datetime(self, faker: Faker) -> None: ...

    @pytest.mark.it("❌  Should raise TypeError for non-serializable objects")
    def test_json_serial_unsupported_type(self) -> None: ...
```

One behaviour per test, and no application logic inside a test. Prefer `parametrize` over loops.

## Async

No `asyncio_mode` is configured, so a coroutine test is never collected on its own: mark it
`@pytest.mark.asyncio` (pytest-asyncio) when it only awaits library code, and
`@pytest.mark.anyio` when it takes the session-scoped `async_client`, whose backend comes from
the `anyio_backend` fixture in `tests/conftest.py`.

Drive the app through `async_client` rather than calling a handler directly whenever the
behaviour depends on being wired into FastAPI: a handler, decorator or middleware that stopped
being applied is invisible to a direct call, and `HttpExceptionsHandler` is only ever exercised
through a request.

## Fixtures

Module level in `tests/fixtures/` when more than one test module needs it, inside the test class
when only one does. A fixture that would take a boolean flag becomes two named ones:
`database_up` and `database_down`, never `database(reachable=False)`.

`faker` (the plugin's own fixture) generates values no assertion depends on. Spell a value out
whenever an assertion reads it back, or the test passes for the wrong reason.

## Doubles

Repositories, handlers and decorators take their collaborators as arguments, so a test hands over
a fake instead of patching. Write the fake as a small class that records what it was asked for,
and it can assert on the calls as well as on the result: that a query stopped at the first hit,
that a session was never opened. `tests/fixtures/common/base_repository_fixtures.py` is the
pattern to follow.

`unittest.mock` — there is no `pytest-mock` here — and `monkeypatch` are for what cannot be
injected: a module-level import, a `staticmethod`, an environment variable, a driver the suite
must not really reach.
