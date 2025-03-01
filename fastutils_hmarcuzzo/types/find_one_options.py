from typing import Any

from sqlalchemy import BinaryExpression
from typing_extensions import TypedDict


class FindOneOptions(TypedDict, total=False):
    select: list[str]
    where: Any | BinaryExpression | None
    order_by: Any
    relations: Any
    having: list[Any]
