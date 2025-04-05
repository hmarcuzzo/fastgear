from fastgear.types.custom_pages import custom_page_query, custom_size_query
from fastgear.types.find_many_options import FindManyOptions
from fastgear.types.pagination import Pagination
from fastgear.utils import PaginationUtils


class SimplePaginationOptions:
    def __call__(
        self, page: int = custom_page_query, size: int = custom_size_query
    ) -> FindManyOptions:
        """Generates pagination options based on the provided page and size.

        Args:
            page (int): The page number for pagination. Defaults to custom_page_query.
            size (int): The size of each page. Defaults to custom_size_query.

        Returns:
            FindManyOptions: The formatted pagination options including skip and take values.

        """
        return PaginationUtils.format_skip_take_options(
            Pagination(skip=page, take=size, sort=[], search=[])
        )
