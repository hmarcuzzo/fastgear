from typing import Any, List, TypedDict, Optional

from sqlalchemy import BinaryExpression


class FindOneOptions(TypedDict, total=False):
    select: List[str]
    where: Optional[Any | BinaryExpression]
    order_by: Any
    relations: Any
