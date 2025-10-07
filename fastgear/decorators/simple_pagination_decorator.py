from fastgear.types.custom_pages import custom_page_query, custom_size_query
from fastgear.types.pagination import Pagination


class SimplePaginationOptions:
    def __call__(self, page: int = custom_page_query, size: int = custom_size_query) -> Pagination:
        """Generates pagination options based on the provided page and size.

        Args:
            page (int): The page number for pagination. Defaults to custom_page_query.
            size (int): The size of each page. Defaults to custom_size_query.

        Returns:
            FindManyOptions: The formatted pagination options including skip and take values.

        """
        return Pagination(
            skip=getattr(page, "default", page),
            take=getattr(size, "default", size),
            sort=[],
            search=[],
            columns=None,
        )
