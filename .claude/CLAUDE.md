# FastGear

Utility library for **FastAPI** projects: generic SQLAlchemy repositories (sync and async),
dynamic query building, offset pagination, Redis client, custom exceptions and handlers,
session management. Published to PyPI and managed with `uv`.

The package lives at the repository root (`fastgear/`, no `src/` layout) and tests import from
`fastgear.*`. SQLAlchemy and Redis are **optional extras**, so the library must stay importable
with neither installed.

## Commands

- `uv sync --all-extras --group test` — install everything the suite needs
- `uv run pytest` — the whole suite; `addopts` already adds coverage and testdox output
- `uvx ruff check .` / `uvx ruff format .` — what CI runs; `ruff-check --fix` and `ruff-format`
  also run on pre-commit (`uv run pre-commit install`)
- `uv run mkdocs serve -f docs/en/mkdocs.yml` — docs site, generated from docstrings

## Layout

| Directory                       | Holds                                                                     |
|:--------------------------------|:--------------------------------------------------------------------------|
| `fastgear/common/database/`     | `AbstractRepository` plus the `sqlalchemy/` and `redis/` implementations   |
| `fastgear/common/schema/`       | pydantic base models and response shapes                                   |
| `fastgear/decorators/`          | route and pagination decorators, `db_session`                              |
| `fastgear/handlers/`            | exception handlers wired into the app                                      |
| `fastgear/middlewares/`         | ASGI middlewares, currently the DB session one                             |
| `fastgear/types/`               | exceptions, enums, pagination and find/update/delete option types          |
| `fastgear/utils/`               | stateless helper classes (`JsonUtils`, `PaginationUtils`, …)               |
| `fastgear/constants/`           | shared literals, e.g. regex expressions                                    |
| `fastgear/_internal/`           | private helpers, not part of the public API                                |

`applications.apply_utils` is the entry point consumers call to attach handlers, pagination and
middlewares to their `FastAPI` instance.

## Optional extras

Anything importing `sqlalchemy` or `redis` is gated, never imported at module top level of a
package that must always load. A package exposes a gated symbol through its `__init__.py`:

```python
if has_extra("sqlalchemy"):
    from .db_session_middleware import DBSessionMiddleware

    __all__ += ["DBSessionMiddleware"]
else:

    def __getattr__(name: str):
        if name in _SQLALCHEMY_SYMBOLS:
            require_extra(name, "sqlalchemy")
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

`require_extra` raises an `ImportError` naming the extra to install, so a missing dependency
fails with an instruction rather than a traceback about a missing module.

## Conventions

- English everywhere: code, comments, docstrings and commit messages.
- `ruff` runs with `select = ["ALL"]` and a curated `ignore` list in `pyproject.toml`, so PEP 8,
  naming, import order and unused imports are enforced by the linter. Never restate a lint rule
  as guidance here; when a rule is genuinely wrong for the project, add it to `ignore` with the
  one-line reason the list already uses.
- Public API is re-exported from the package `__init__.py` with an explicit `__all__`, so callers
  import from the package and not from the module.
- Writing a commit message: follow the `commit-message` skill.
