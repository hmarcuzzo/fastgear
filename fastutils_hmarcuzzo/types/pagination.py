from typing import TypedDict


class Pagination(TypedDict):
    skip: int
    take: int
