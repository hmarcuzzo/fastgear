import typing
from math import ceil
from typing import Any

from loguru import logger
from pydantic import BaseModel, TypeAdapter, ValidationError
from pydantic.fields import FieldInfo

from fastgear.types.custom_pages import Page
from fastgear.types.generic_types_var import (
    ColumnsQueryType,
    EntityType,
    FindAllQueryType,
    OrderByQueryType,
)
from fastgear.types.http_exceptions import BadRequestException
from fastgear.types.pagination import Pagination, PaginationSearch, PaginationSort


class PaginationUtils:
    def build_pagination_options(
        self,
        page: int,
        size: int,
        search: list[str] | None,
        search_all: str | None,
        sort: list[str] | None,
        columns: list[str] | None,
        columns_query: ColumnsQueryType,
        find_all_query: FindAllQueryType = None,
        order_by_query: OrderByQueryType = None,
    ) -> Pagination:
        """Build pagination options from query parameters

        Deduplicates and parses sort/search parameters, producing a Pagination
        mapping with skip, take, and normalized sort/search entries. When
        query schemas are provided, validates sort fields/directions and search
        fields/values against the corresponding Pydantic models.

        Args:
            page (int): 1-based page number used to populate the `skip` field.
            size (int): Page size used to populate the `take` field.
            search (list[str] | None): List of filters in the form "field:value". Duplicates are removed.
            search_all (str | None): Global search string applied to all searchable fields.
            sort (list[str] | None): List of sort directives in the form "field:ASC|DESC". Duplicates are removed.
            columns (list[str] | None): List of selected columns. Duplicates are removed.
            columns_query (ColumnsQueryType): Pydantic model type used to validate selectable columns.
            find_all_query (FindAllQueryType, optional): Pydantic model type used to validate search fields and values.
            order_by_query (OrderByQueryType, optional): Pydantic model type used to validate sortable fields and directions.

        Returns:
            Pagination: A pagination options mapping with keys `skip`, `take`,
            and optional `sort`/`search` lists ready for downstream processing.

        Raises:
            BadRequestException: If sort or search filters are invalid given the
            provided query schemas.
        """
        paging_options = {"skip": page, "take": size, "sort": [], "search": [], "columns": []}

        if sort:
            sort = list(set(sort))
            paging_options["sort"].extend(self._create_pagination_sort(sort))
            self._check_and_raise_for_invalid_sort_filters(paging_options["sort"], order_by_query)

        if search:
            search = list(set(search))
            paging_options["search"].extend(self._create_pagination_search(search))
            self._check_and_raise_for_invalid_search_filters(
                paging_options["search"], find_all_query
            )

        if search_all:
            paging_options["search"].extend(
                [
                    self._create_pagination_search(
                        [f"{column}:{search_all}" for column in find_all_query.model_fields]
                    )
                ]
            )

        columns = list(set(columns)) if columns else []
        paging_options["columns"] = self.select_columns(columns, columns_query)

        return Pagination(**paging_options)

    @staticmethod
    def select_columns(columns: list[str], columns_query: ColumnsQueryType) -> list[str]:
        if PaginationUtils.is_valid_column_selection(columns, columns_query):
            return PaginationUtils.merge_with_required_columns(columns, columns_query)

        message = f"Invalid columns: {columns}"
        logger.info(message)
        raise BadRequestException(message)

    @staticmethod
    def _create_pagination_sort(sort_params: list[str]) -> list[PaginationSort]:
        return [
            PaginationSort(field=field, by=by)
            for field, by in (param.split(":", 1) for param in sort_params)
        ]

    @staticmethod
    def _create_pagination_search(search_params: list[str]) -> list[PaginationSearch]:
        return [
            PaginationSearch(field=field, value=value)
            for field, value in (param.split(":", 1) for param in search_params)
        ]

    @staticmethod
    def _check_and_raise_for_invalid_sort_filters(
        pagination_sorts: list[PaginationSort], order_by_query: OrderByQueryType = None
    ) -> None:
        if order_by_query and not PaginationUtils._is_valid_sort_params(
            pagination_sorts, order_by_query
        ):
            message = f"Invalid sort filters: {pagination_sorts}"
            logger.info(message)
            raise BadRequestException(message)

    @staticmethod
    def _check_and_raise_for_invalid_search_filters(
        pagination_search: list[PaginationSearch], find_all_query: FindAllQueryType = None
    ) -> None:
        if find_all_query and not PaginationUtils._is_valid_search_params(
            pagination_search, find_all_query
        ):
            raise BadRequestException("Invalid search filters")

    @staticmethod
    def _is_valid_sort_params(
        sort: list[PaginationSort], order_by_query_schema: OrderByQueryType
    ) -> bool:
        query_schema_fields = order_by_query_schema.model_fields

        is_valid_field = all(sort_param["field"] in query_schema_fields for sort_param in sort)
        is_valid_direction = all(sort_param["by"] in ["ASC", "DESC"] for sort_param in sort)

        return is_valid_field and is_valid_direction

    @staticmethod
    def _is_valid_search_params(
        search: list[PaginationSearch], find_all_query: FindAllQueryType
    ) -> bool:
        query_dto_fields = find_all_query.model_fields

        if not PaginationUtils.validate_required_search_filter(search, query_dto_fields):
            return False

        try:
            search_params = PaginationUtils.aggregate_values_by_field(search, find_all_query)
        except KeyError as e:
            logger.info(f"Invalid search filter: {e}")
            raise BadRequestException(f"Invalid search filters: {e}")

        for search_param in search_params:
            if search_param["field"] not in query_dto_fields:
                return False

            PaginationUtils.assert_search_param_convertible(find_all_query, search_param)

        return True

    @staticmethod
    def validate_required_search_filter(
        search: list[PaginationSearch], query_dto_fields: dict[str, FieldInfo]
    ) -> bool:
        search_fields = [search_param["field"] for search_param in search]
        for field, field_info in query_dto_fields.items():
            if field_info.is_required() and field not in search_fields:
                return False

        return True

    @staticmethod
    def is_valid_column_selection(columns: list[str], columns_query_dto: ColumnsQueryType) -> bool:
        query_dto_fields = columns_query_dto.model_fields

        return all(column in query_dto_fields for column in columns)

    @staticmethod
    def merge_with_required_columns(
        columns: list[str], columns_query_dto: ColumnsQueryType
    ) -> list[str]:
        query_dto_fields = columns_query_dto.model_fields

        for field, field_info in query_dto_fields.items():
            if field_info.is_required() and field not in columns:
                columns.append(field)

        return columns

    @staticmethod
    def to_page_response(
        items: list[EntityType | BaseModel], total: int, offset: int, size: int
    ) -> Page[EntityType | BaseModel]:
        """
        Construct a Page value object containing the items for the current page
        together with pagination metadata derived from the supplied parameters.

        Args:
            items (list[EntityType | BaseModel]): Items belonging to the current page.
            total (int): Total number of items available across all pages.
            offset (int): Number of items skipped (offset). This method treats `skip`
                as an offset (0-based count of items to skip).
            size (int): Number of items per page.

        Returns:
            Page[EntityType | BaseModel]: A Page object containing the items and
            pagination metadata.

        Notes:
            - This function does not perform validation of arguments (e.g. negative
              values or zero page_size). Callers should validate inputs before use.
        """
        current_page = offset // size + 1

        return Page(
            items=items, page=current_page, size=size, total=total, pages=ceil(total / size)
        )

    @staticmethod
    def assert_no_blocked_attributes(
        block_attributes: list[str],
        search: list | None,
        sort: list | None,
        columns: list | None,
        search_all: str | None,
    ) -> None:
        """Assert that blocked pagination attributes are not present

        Checks whether any of the provided pagination attributes are present and,
        if so, logs the blocked attributes and raises BadRequestException.

        Args:
            block_attributes (list[str]): Attributes that are blocked for the route.
            search (list | None): Search filters provided by the request.
            sort (list | None): Sort directives provided by the request.
            columns (list | None): Selected columns provided by the request.
            search_all (str | None): Global search string provided by the request.

        Returns:
            None: This function only raises on violation.

        Raises:
            BadRequestException: If any blocked attribute is present in the request.
        """
        attributes_map = {
            "search": search,
            "sort": sort,
            "columns": columns,
            "search_all": search_all,
        }
        blocked = [attr for attr in block_attributes if attributes_map.get(attr) is not None]
        if not blocked:
            return

        logger.info(f"Invalid block attribute(s): {blocked}")
        raise BadRequestException(
            f"The attribute(s) {blocked} are blocked in this route and cannot be used.", loc=blocked
        )

    @staticmethod
    def assert_search_param_convertible(
        find_all_query: FindAllQueryType, search_param: PaginationSearch
    ) -> bool:
        """Validate that a search parameter value is convertible to the query type

        Attempt to validate the single-field mapping {field: value} against the provided
        Pydantic find_all_query using TypeAdapter.validate_python. On success returns
        True; on conversion failure raises BadRequestException.

        Args:
            find_all_query (FindAllQueryType): Pydantic model class describing expected field types.
            search_param (PaginationSearch): Mapping with field (str) and value (str) to validate.

        Returns:
            bool: True if the value can be converted to the expected type.

        Raises:
            BadRequestException: If the value is invalid or cannot be converted.
        """
        try:
            TypeAdapter(find_all_query).validate_python(
                {search_param["field"]: search_param["value"]}
            )
            return True
        except (ValueError, TypeError, ValidationError) as e:
            logger.info(f"Invalid search value: {e}")
            raise BadRequestException(f"Invalid search value: {e}")

    @staticmethod
    def aggregate_values_by_field(
        entries: list[PaginationSearch], find_all_query: FindAllQueryType
    ) -> list[PaginationSearch]:
        """Aggregates values by field from a list of pagination search entries.

        Args:
            entries (List[PaginationSearch]): A list of pagination search entries, each containing
            a field and value.
            find_all_query (FindAllQueryType): The query object that defines the expected types for the fields.

        Returns:
            List[PaginationSearch]: A list of PaginationSearch where each element contains a field and its aggregated values.
        """
        query_attr_types = typing.get_type_hints(find_all_query)
        aggregated: dict[str, str | list[str]] = {}

        for entry in entries:
            field, value = entry["field"], entry["value"]
            field_is_list = PaginationUtils._is_list_type_hint(query_attr_types.get(field))

            if field in aggregated:
                if isinstance(aggregated[field], list):
                    aggregated[field].append(value)
                else:
                    aggregated[field] = [aggregated[field], value]
            else:
                aggregated[field] = [value] if field_is_list else value

        return [{"field": f, "value": v} for f, v in aggregated.items()]

    @staticmethod
    def _is_list_type_hint(field_type: Any) -> bool:
        """Return whether the given type hint represents a list.

        Args:
            field_type (Any): A type hint to inspect (for example from typing.get_type_hints).

        Returns:
            bool: True if the origin of the type hint is `list`, otherwise False.

        Examples:
            >>> PaginationUtils._is_list_type_hint(list[int])
            True
        """
        return typing.get_origin(field_type) is list
