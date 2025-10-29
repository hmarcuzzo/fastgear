from typing import Any

from sqlalchemy import BinaryExpression
from typing_extensions import TypedDict


class UpdateOptions(TypedDict, total=False):
    where: Any | BinaryExpression | None
