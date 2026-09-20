---
paths:
  - "fastgear/**/*.py"
  - "tests/**/*.py"
---

# Python style

`ruff` already enforces PEP 8, naming, import order and unused imports. What follows is what the
linter cannot check, plus the rules its `ignore` list deliberately switched off.

## Types

Annotate everything: parameters, return values and class attributes, in tests as much as in
library code. `ANN` sits in ruff's `ignore` list, so nothing catches a missing annotation for
you, and the published documentation renders the signature as written.

Skip the annotation only where the assignment already states the type (`app: FastAPI = FastAPI()`
is noise). Use `Self` for a method returning its own instance, `TypeVar`s declared next to the
generic they parametrise (`EntityType`, `SessionType`), and a `typing.Protocol` — not a bare
`Callable` — for a callable with keyword or optional arguments, so the signature stays visible.

## Modules

One concept per module, named in `snake_case` after the class it holds: `PaginationUtils` lives
in `utils/pagination_utils.py`. Keep modules under 400 lines and functions under 50 — `C901` and
`PLR` are ignored, so complexity is on the author.

A package's `__init__.py` re-exports its public names and declares `__all__`, so callers import
from the package rather than the module:

```python
from .logger_utils import LoggerUtils

__all__ = ["LoggerUtils"]
```

Anything that imports `sqlalchemy` or `redis` is gated behind `has_extra` / `require_extra` from
`fastgear._internal.import_utils`, as `CLAUDE.md` shows. A top-level import of an extra in a
module that always loads breaks every consumer who installed `fastgear` without it.

`fastgear/_internal/` is private: nothing there is re-exported, and a consumer importing from it
gets no compatibility guarantee.

## Errors

Catch the narrowest concrete exception, never bare `Exception`, and re-raise with `raise ... from`
to keep the cause. Library errors subclass `types.custom_base_exception.CustomBaseException`,
which carries the `status_code` that `HttpExceptionsHandler` turns into a response; a new error
belongs in `types/http_exceptions.py` next to the others, not raised as a raw `HTTPException`.

## Logging

Log through the library's logger, bound to the module that emits the record
(`logger.bind(name=self.__class__.__module__)`), never `print`. `LoggerUtils.configure_logging`
in `utils/logger_utils.py` owns the configuration, so it is the only place that touches the
logger's sinks or format. `G004` is ignored, so an f-string in a log call is fine.

## Comments and docstrings

The public API is documented through `mkdocstrings`, so a public class, method or function that
consumers call carries a Google-style docstring: summary line in the imperative under 72
characters, then `Args`, `Returns`, `Yields`, `Raises`, `Examples`, `Notes` in that order, with
the type in parentheses beside each argument name. Update it whenever the signature or the
behaviour it describes changes — a stale docstring ships to the docs site.

Private helpers, `_internal/` and tests need none. Never write a docstring or comment that
restates the signature; write one when it records something the code cannot say on its own: why
a workaround exists, what a non-obvious constraint is, what a deliberate omission means.
