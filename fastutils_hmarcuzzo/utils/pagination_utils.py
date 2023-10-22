from math import ceil
from typing import TypeVar, List

from starlette.requests import Request

from fastutils_hmarcuzzo.types.custom_pages import Page
from fastutils_hmarcuzzo.types.find_many_options import FindManyOptions
from fastutils_hmarcuzzo.types.pagination import Pagination

T = TypeVar("T")


class PaginationUtils:
    @staticmethod
    def get_pagination_from_request(request: Request) -> Pagination:
        request_params = request.query_params
        page = request_params.get("page")
        size = request_params.get("size")

        if page is None or size is None:
            raise ValueError("Pagination params not found")

        return Pagination(skip=int(page), take=int(size))

    @staticmethod
    def format_pagination_options(
        paging_params: Pagination,
    ) -> FindManyOptions:
        paging_data = FindManyOptions(
            skip=(paging_params["skip"] - 1) * paging_params["take"],
            take=paging_params["take"],
        )

        return paging_data

    @staticmethod
    def generate_page(items: List[T], total: int, skip: int, page_size: int) -> Page[T]:
        current_page = skip // page_size + 1

        return Page(
            items=items,
            page=current_page,
            size=page_size,
            total=total,
            pages=ceil(total / page_size),
        )
