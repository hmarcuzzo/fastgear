from fastutils_hmarcuzzo.types.custom_pages import custom_size_query, custom_page_query
from fastutils_hmarcuzzo.types.find_many_options import FindManyOptions
from fastutils_hmarcuzzo.types.pagination import Pagination
from fastutils_hmarcuzzo.utils.pagination_utils import PaginationUtils


class SimplePaginationOptions(object):
    def __call__(
        self, page: int = custom_page_query, size: int = custom_size_query
    ) -> FindManyOptions:
        return PaginationUtils.format_skip_take_options(Pagination(skip=page, take=size))
