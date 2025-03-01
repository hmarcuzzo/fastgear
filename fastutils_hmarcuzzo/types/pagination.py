from typing_extensions import TypedDict


class PaginationSearch(TypedDict):
    field: str
    value: str


class PaginationSort(TypedDict):
    field: str
    by: str


class Pagination(TypedDict):
    skip: int
    take: int
    sort: list[PaginationSort]
    search: list[PaginationSearch]
