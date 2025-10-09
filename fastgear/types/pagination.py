from dataclasses import dataclass

from typing_extensions import TypedDict


class PaginationSearch(TypedDict):
    field: str
    value: str


class PaginationSort(TypedDict):
    field: str
    by: str


@dataclass(slots=True, frozen=True)
class Pagination:
    skip: int
    take: int
    sort: list[PaginationSort]
    search: list[PaginationSearch | list[PaginationSearch]]
    columns: list[str]

    def __post_init__(self):
        # Convert page number to zero-based index for skip
        new_skip = (self.skip - 1) * self.take
        object.__setattr__(self, "skip", new_skip)
