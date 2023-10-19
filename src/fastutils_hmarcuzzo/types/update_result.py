from typing import Any, TypedDict


class UpdateResult(TypedDict):
    raw: Any
    affected: int
    generatedMaps: Any
