from typing import Any

from typing_extensions import TypedDict


class UpdateResult(TypedDict):
    raw: Any
    affected: int
    generated_maps: Any
