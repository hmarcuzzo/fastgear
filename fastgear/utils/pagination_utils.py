import logging
import typing
from math import ceil
from typing import Any, TypeVar

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

logger = logging.getLogger(__name__)


class PaginationUtils:
    def generate_paging_parameters(
        self,
        page: int,
        size: int,
        search: list[str] | None,
        sort: list[str] | None,
        find_all_query: F = None,
        order_by_query: OB = None,
    ) -> Pagination:
        paging_options = Pagination(skip=page, take=size, sort=[], search=[])

        if sort:
            sort = self._remove_duplicate_params(sort)
            paging_options["sort"] = self._create_pagination_sort(sort)
            self._check_and_raise_for_invalid_sort_filters(paging_options["sort"], order_by_query)

        if search:
            search = self._remove_duplicate_params(search)
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

        where_columns = find_all_query.__fields__ if find_all_query else get_columns(entity).keys()

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
            (paging_options, selected_columns) = (
                PaginationUtils.generating_selected_relationships_and_columns(
                    paging_options, list(set(selected_columns)), columns_query, entity
                )
            )
        else:
            message = f"Invalid columns: {selected_columns}"
            logger.info(message)
            raise BadRequestException(message)

    @staticmethod
    def format_skip_take_options(paging_options: Pagination) -> FindManyOptions:
        return FindManyOptions(
            skip=(paging_options["skip"] - 1) * paging_options["take"], take=paging_options["take"]
        )

    @staticmethod
    def _remove_duplicate_params(params: list[str]) -> list[str]:
        return list(set(params))

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
        query_schema_fields = order_by_query_schema.__fields__

        is_valid_field = all(sort_param["field"] in query_schema_fields for sort_param in sort)
        is_valid_direction = all(sort_param["by"] in ["ASC", "DESC"] for sort_param in sort)

        return is_valid_field and is_valid_direction

    @staticmethod
    def _is_valid_search_params(search: list[PaginationSearch], find_all_query: F) -> bool:
        query_dto_fields = find_all_query.__fields__

        if not PaginationUtils.validate_required_search_filter(search, query_dto_fields):
            return False

        try:
            search_params = PaginationUtils.aggregate_values_by_field(search, find_all_query)
        except KeyError as e:
            logger.info(f"Invalid search filter: {e}")
            raise BadRequestException(f"Invalid search filters: {e}")
        for search_param in search_params:
            if (
                search_param["field"] not in query_dto_fields
                or PaginationUtils.can_convert(find_all_query, search_param) is False
            ):
                return False

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
        query_dto_fields = columns_query_dto.__fields__

        return all(column in query_dto_fields for column in columns)

    @staticmethod
    def generating_selected_relationships_and_columns(
        paging_options: FindManyOptions,
        selected_columns: list[str],
        columns_query_dto: ColumnsQueryType,
        entity: EntityType,
    ) -> (FindManyOptions, list[str]):
        query_dto_fields = columns_query_dto.__fields__
        entity_relationships = inspect(entity).relationships

        for field in query_dto_fields:
            if field in entity_relationships:
                if query_dto_fields[field].is_required() or field in selected_columns:
                    paging_options.setdefault("relations", []).append(field)
                    selected_columns.remove(field) if field in selected_columns else None
                    column_name = list(entity_relationships[field].local_columns)[0].name
                    selected_columns.append(getattr(entity, column_name))

            elif query_dto_fields[field].is_required() and field not in selected_columns:
                selected_columns.append(getattr(entity, field, field))

        for column in selected_columns:
            if isinstance(column, str) and hasattr(entity, column):
                selected_columns[selected_columns.index(column)] = getattr(entity, column)

        if not paging_options.get("relations"):
            paging_options.pop("relations", None)

        paging_options["select"] = paging_options.get("select", []) + selected_columns
        if not paging_options.get("select"):
            paging_options.pop("select", None)

        return paging_options, selected_columns

    @staticmethod
    def generate_page(
        items: list[EntityType | BaseModel], total: int, skip: int, page_size: int
    ) -> Page[EntityType | BaseModel]:
        current_page = skip // page_size + 1

        return Page(
            items=items,
            page=current_page,
            size=page_size,
            total=total,
            pages=ceil(total / page_size),
        )

    @staticmethod
    def validate_block_attributes(
        block_attributes: list[str],
        search: list | None,
        sort: list | None,
        columns: list | None,
        search_all: str | None,
    ) -> None:
        attributes = {"search": search, "sort": sort, "columns": columns, "search_all": search_all}

        for attribute in block_attributes:
            if attribute in attributes and attributes[attribute] is not None:
                logger.info(f"Invalid block attribute: {attribute}")
                raise BadRequestException(
                    f"The attribute '{attribute}' is blocked in this route and cannot be used.",
                    loc=[attribute],
                )

    @staticmethod
    def can_convert(find_all_query: F, search_param: PaginationSearch) -> bool:
        """Validates if the search parameter can be converted to the type defined
        in the find_all_query.

        Args:
            find_all_query (F): The query object that defines the expected types.
            search_param (PaginationSearch): The search parameter containing the field and value
            to be validated.

        Returns:
            bool: True if the search parameter can be converted to the expected type,
            False otherwise.

        Raises:
            BadRequestException: If the search value is invalid or cannot be converted.

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
                    [value] if PaginationUtils._is_list_type(query_attr_types[field]) else value
                )

        return [{"field": key, "value": aggregated[key]} for key in aggregated]

    @staticmethod
    def _is_list_type(field_type: Any) -> bool:
        return (
            getattr(field_type, "__origin__", None) is list
            or getattr(field_type, "__origin__", None) is list
        )
