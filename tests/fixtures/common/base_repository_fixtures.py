from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import pytest
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from fastgear.common.database.sqlalchemy.session import db_session


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

    def all(self) -> list[Any]:
        return list(self._all_rows or [])


# ---- Sample entity ----
@dataclass
class UserEntity:
    id: str
    name: str
