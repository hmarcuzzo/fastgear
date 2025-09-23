import typing
import warnings
from math import ceil
from typing import Any, TypeVar

from loguru import logger
from pydantic import BaseModel, TypeAdapter
from sqlalchemy import String, asc, cast, desc, inspect, or_
from sqlalchemy_utils import cast_if, get_columns

from fastgear.types.custom_pages import Page
from fastgear.types.find_many_options import FindManyOptions
from fastgear.types.generic_types_var import ColumnsQueryType, EntityType
from fastgear.types.http_exceptions import BadRequestException
from fastgear.types.pagination import Pagination, PaginationSearch, PaginationSort

F = TypeVar("F")
OB = TypeVar("OB")


class PaginationUtils:
    def build_pagination_options(
        self,
        page: int,
        size: int,
        search: list[str] | None,
        sort: list[str] | None,
        find_all_query: F = None,
        order_by_query: OB = None,
    ) -> Pagination:
        """Build pagination options from query parameters

        Deduplicates and parses sort/search parameters, producing a Pagination
        mapping with skip, take, and normalized sort/search entries. When
        query schemas are provided, validates sort fields/directions and search
        fields/values against the corresponding Pydantic models.

        Args:
            page (int): 1-based page number used to populate the `skip` field.
            size (int): Page size used to populate the `take` field.
            search (list[str] | None): List of filters in the form
                "field:value". Duplicates are removed.
            sort (list[str] | None): List of sort directives in the form
                "field:ASC|DESC". Duplicates are removed.
            find_all_query (F, optional): Pydantic model type used to validate
                search fields and values.
            order_by_query (OB, optional): Pydantic model type used to validate
                sortable fields and directions.

        Returns:
            Pagination: A pagination options mapping with keys `skip`, `take`,
            and optional `sort`/`search` lists ready for downstream processing.

        Raises:
            BadRequestException: If sort or search filters are invalid given the
            provided query schemas.
        """
        paging_options = Pagination(skip=page, take=size, sort=[], search=[])

        if sort:
            sort = list(set(sort))
            paging_options["sort"] = self._create_pagination_sort(sort)
            self._check_and_raise_for_invalid_sort_filters(paging_options["sort"], order_by_query)

        if search:
            search = list(set(search))
            paging_options["search"] = self._create_pagination_search(search)
            self._check_and_raise_for_invalid_search_filters(
                paging_options["search"], find_all_query
            )

        return paging_options

    def get_paging_data(
        self,
        entity: EntityType,
        paging_options: Pagination,
        columns: list[str],
        search_all: str | None,
        columns_query: ColumnsQueryType,
        find_all_query: F | None = None,
    ) -> FindManyOptions:
        formatted_skip_take = self.format_skip_take_options(paging_options)

        paging_data = FindManyOptions(select=[], where=[], order_by=[], relations=[])

        self.sort_data(paging_options, entity, paging_data)
        self.search_data(paging_options, entity, paging_data)
        self.search_all_data(entity, paging_data, search_all, find_all_query)
        self.select_columns(columns, columns_query, entity, paging_data)

        return {**paging_data, **formatted_skip_take}

    @staticmethod
    def sort_data(
        paging_options: Pagination, entity: EntityType, paging_data: FindManyOptions
    ) -> None:
        if "sort" not in paging_options:
            return

        for sort_param in paging_options["sort"]:
            sort_obj = sort_param["field"]

            if hasattr(entity, sort_obj):
                sort_obj = getattr(entity, sort_obj)

            order = asc(sort_obj) if sort_param["by"] == "ASC" else desc(sort_obj)
            paging_data["order_by"].append(order)

    @staticmethod
    def search_data(
        paging_options: Pagination, entity: EntityType, paging_data: FindManyOptions
    ) -> None:
        if "search" not in paging_options:
            return

        for search_param in paging_options["search"]:
            condition = search_param

            if hasattr(entity, search_param["field"]):
                search_obj = getattr(entity, search_param["field"])
                condition = cast_if(search_obj, String).ilike(f"%{search_param['value']}%")

            paging_data["where"].append(condition)

    @staticmethod
    def search_all_data(
        entity: EntityType,
        paging_data: FindManyOptions,
        search_all: str = None,
        find_all_query: F = None,
    ) -> None:
        if not search_all:
            return

        where_columns = (
            find_all_query.model_fields if find_all_query else get_columns(entity).keys()
        )

        where_clauses = [
            cast(getattr(entity, column), String).ilike(f"%{search_all}%")
            if hasattr(entity, column)
            else {"field": column, "value": search_all}
            for column in where_columns
        ]
        paging_data.setdefault("where", []).append(
            or_(*where_clauses)
            if not any(isinstance(where_clause, dict) for where_clause in where_clauses)
            else where_clauses
        )

    @staticmethod
    def select_columns(
        selected_columns: list[str],
        columns_query: ColumnsQueryType,
        entity: EntityType,
        paging_options: FindManyOptions,
    ) -> None:
        if PaginationUtils.validate_columns(list(set(selected_columns)), columns_query):
            (_, _) = PaginationUtils.resolve_selected_columns_and_relations(
                paging_options, list(set(selected_columns)), columns_query, entity
            )
        else:
            message = f"Invalid columns: {selected_columns}"
            logger.info(message)
            raise BadRequestException(message)

    @staticmethod
    def format_skip_take_options(paging_options: Pagination) -> FindManyOptions:
        def extract_value(val: object) -> object:
            return getattr(val, "default", val)

        skip = int(extract_value(paging_options["skip"]))
        take = int(extract_value(paging_options["take"]))
        return FindManyOptions(skip=(skip - 1) * take, take=take)

    @staticmethod
    def _create_pagination_sort(sort_params: list[str]) -> list[PaginationSort]:
        pagination_sorts = []
        for sort_param in sort_params:
            sort_param_split = sort_param.split(":", 1)
            pagination_sorts.append(
                PaginationSort(field=sort_param_split[0], by=sort_param_split[1])
            )
        return pagination_sorts

    @staticmethod
    def _create_pagination_search(search_params: list[str]) -> list[PaginationSearch]:
        pagination_search = []
        for search_param in search_params:
            search_param_split = search_param.split(":", 1)
            pagination_search.append(
                PaginationSearch(field=search_param_split[0], value=search_param_split[1])
            )
        return pagination_search

    @staticmethod
    def _check_and_raise_for_invalid_sort_filters(
        pagination_sorts: list[PaginationSort], order_by_query: OB = None
    ) -> None:
        if order_by_query and not PaginationUtils._is_valid_sort_params(
            pagination_sorts, order_by_query
        ):
            message = f"Invalid sort filters: {pagination_sorts}"
            logger.info(message)
            raise BadRequestException(message)

    @staticmethod
    def _check_and_raise_for_invalid_search_filters(
        pagination_search: list[PaginationSearch], find_all_query: F = None
    ) -> None:
        if find_all_query and not PaginationUtils._is_valid_search_params(
            pagination_search, find_all_query
        ):
            raise BadRequestException("Invalid search filters")

    @staticmethod
    def _is_valid_sort_params(sort: list[PaginationSort], order_by_query_schema: OB) -> bool:
        query_schema_fields = order_by_query_schema.model_fields

        is_valid_field = all(sort_param["field"] in query_schema_fields for sort_param in sort)
        is_valid_direction = all(sort_param["by"] in ["ASC", "DESC"] for sort_param in sort)

        return is_valid_field and is_valid_direction

    @staticmethod
    def _is_valid_search_params(search: list[PaginationSearch], find_all_query: F) -> bool:
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
        search: list[PaginationSearch], query_dto_fields: F
    ) -> bool:
        search_fields = [search_param["field"] for search_param in search]
        for field in query_dto_fields:
            if query_dto_fields[field].is_required() and field not in search_fields:
                return False

        return True

    @staticmethod
    def validate_columns(columns: list[str], columns_query_dto: ColumnsQueryType) -> bool:
        query_dto_fields = columns_query_dto.model_fields

        return all(column in query_dto_fields for column in columns)

    @staticmethod
    def resolve_selected_columns_and_relations(
        paging_options: FindManyOptions,
        selected_columns: list[str],
        columns_query_dto: ColumnsQueryType,
        entity: EntityType,
    ) -> (FindManyOptions, list[str]):
        query_dto_fields = columns_query_dto.model_fields
        entity_relationships = inspect(entity).relationships

        relations = []
        columns = []

        for field, field_info in query_dto_fields.items():
            if field in entity_relationships:
                if field_info.is_required() or field in selected_columns:
                    relations.append(field)
                    if field in selected_columns:
                        selected_columns.remove(field)
            elif field_info.is_required() and field not in selected_columns:
                columns.append(getattr(entity, field, field))

        for column in selected_columns:
            columns.extend(
                [
                    getattr(entity, column)
                    if isinstance(column, str) and hasattr(entity, column)
                    else column
                ]
            )

        if relations:
            paging_options["relations"] = relations
        else:
            paging_options.pop("relations", None)

        if columns:
            paging_options["select"] = paging_options.get("select", []) + columns
        else:
            paging_options.pop("select", None)

        return paging_options, selected_columns

    @staticmethod
    def generate_page(
        items: list[EntityType | BaseModel], total: int, offset: int, size: int
    ) -> Page[EntityType | BaseModel]:
        """Deprecated: use `to_page_response` instead.

        Deprecated:
            This function is deprecated and will be removed in a future release.
            Use PaginationUtils.to_page_response(items, total, offset, size).
        """
        warnings.warn(
            "generate_page() is deprecated and will be removed in a future release. ",
            DeprecationWarning,
            stacklevel=2,
        )
        return PaginationUtils.to_page_response(items, total, offset, size)

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
    def assert_search_param_convertible(find_all_query: F, search_param: PaginationSearch) -> bool:
        """Validate that a search parameter value is convertible to the query type

        Attempt to validate the single-field mapping {field: value} against the provided
        Pydantic find_all_query using TypeAdapter.validate_python. On success returns
        True; on conversion failure raises BadRequestException.

        Args:
            find_all_query (F): Pydantic model class describing expected field types.
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
        except (ValueError, TypeError) as e:
            logger.info(f"Invalid search value: {e}")
            raise BadRequestException(f"Invalid search value: {e}")

    @staticmethod
    def aggregate_values_by_field(
        entries: list[PaginationSearch], find_all_query: F
    ) -> list[dict[str, str | list[str]]]:
        """Aggregates values by field from a list of pagination search entries.

        Args:
            entries (List[PaginationSearch]): A list of pagination search entries, each containing
            a field and value.
            find_all_query (F): The query object that defines the expected types for the fields.

        Returns:
            List[Dict[str, str | List[str]]]: A list of dictionaries where each dictionary contains
             a field and its aggregated values.

        """
        query_attr_types = typing.get_type_hints(find_all_query)
        aggregated = {}
        for entry in entries:
            field, value = entry["field"], entry["value"]
            if field in aggregated:
                if isinstance(aggregated[field], list):
                    aggregated[field].append(value)
                else:
                    aggregated[field] = [aggregated[field], value]
            else:
                aggregated[field] = (
                    [value]
                    if PaginationUtils._is_list_type_hint(query_attr_types[field])
                    else value
                )

        return [{"field": key, "value": aggregated[key]} for key in aggregated]

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
