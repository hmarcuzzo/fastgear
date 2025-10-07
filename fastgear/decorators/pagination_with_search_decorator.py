from typing import Annotated, Literal

from fastapi import Query
from pydantic import constr

from fastgear.constants import regex
from fastgear.decorators.simple_pagination_decorator import SimplePaginationOptions
from fastgear.types.custom_pages import custom_page_query, custom_size_query
from fastgear.types.generic_types_var import ColumnsQueryType, FindAllQueryType, OrderByQueryType
from fastgear.types.pagination import Pagination
from fastgear.utils import PaginationUtils

SearchString = constr(pattern=f"^{regex.ANY_CHAR}:{regex.ANY_CHAR}$")
SortString = constr(pattern=f"^{regex.ANY_CHAR}:{regex.ORDER_BY_QUERY}")
ColumnsString = constr(pattern=f"^{regex.ANY_CHAR}$")


class PaginationWithSearchOptions(SimplePaginationOptions):
    def __init__(
        self,
        columns_query: ColumnsQueryType,
        find_all_query: FindAllQueryType = None,
        order_by_query: OrderByQueryType = None,
        block_attributes: list[Literal["search", "sort", "columns", "search_all"]] = None,
    ) -> None:
        """Initializes the PaginationWithSearchOptions class.

        This constructor sets up the pagination options with search capabilities for a given entity.
        It initializes the entity, columns query, find all query, order by query, and block attributes.

        Args:
            columns_query (ColumnsQueryType): The query for selecting specific columns.
            find_all_query (FindAllQueryType, optional): The query for finding all records. Defaults to None.
            order_by_query (OrderByQueryType, optional): The query for ordering the records. Defaults to None.
            block_attributes (List[Literal["search", "sort", "columns", "search_all"]], optional):
                A list of attributes to block from being used in the pagination options. Defaults to an empty list.

        """
        if block_attributes is None:
            block_attributes = []
        self.columns_query = columns_query
        self.find_all_query = find_all_query
        self.order_by_query = order_by_query
        self.block_attributes = block_attributes

        self.pagination_utils = PaginationUtils()

    def __call__(
        self,
        page: int = custom_page_query,
        size: int = custom_size_query,
        search: Annotated[list[SearchString] | None, Query(examples=["field:value"])] = None,
        sort: Annotated[list[SortString] | None, Query(examples=["field:by"])] = None,
        columns: Annotated[list[ColumnsString] | None, Query(examples=["field"])] = None,
        search_all: Annotated[
            str | None, Query(pattern=f"^{regex.ANY_CHAR}$", examples=["value"])
        ] = None,
    ) -> Pagination:
        """Generates pagination and search options.

        This method is called to create a `FindManyOptions` object that includes pagination, sorting,
        column selection, and search parameters based on the provided arguments.

        Args:
            page (int, optional): The page number for pagination. Defaults to `custom_page_query`.
            size (int, optional): The number of items per page. Defaults to `custom_size_query`.
            search (Annotated[List[SearchString] | None, Query], optional): A list of search
                strings in the format "field:value". Defaults to None.
            sort (Annotated[List[SortString] | None, Query], optional): A list of sort strings in the format
                "field:by". Defaults to None.
            columns (Annotated[List[ColumnsString] | None, Query], optional): A list of columns to
                include in the result. Defaults to None.
            search_all (Annotated[str | None, Query], optional): A global search string to apply
                to all fields. Defaults to None.

        Returns:
            FindManyOptions: An object containing the pagination and search options.

        """
        self.pagination_utils.assert_no_blocked_attributes(
            self.block_attributes, search, sort, columns, search_all
        )

        return self.pagination_utils.build_pagination_options(
            page,
            size,
            search,
            search_all,
            sort,
            columns,
            self.columns_query,
            self.find_all_query,
            self.order_by_query,
        )
