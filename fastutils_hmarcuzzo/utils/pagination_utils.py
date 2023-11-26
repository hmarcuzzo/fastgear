from math import ceil
from typing import TypeVar, List

from sqlalchemy import String, or_, inspect, cast
from sqlalchemy_utils import cast_if, get_columns

from fastutils_hmarcuzzo.types.custom_pages import Page
from fastutils_hmarcuzzo.types.exceptions import BadRequestException
from fastutils_hmarcuzzo.types.find_many_options import FindManyOptions
from fastutils_hmarcuzzo.types.pagination import Pagination, PaginationSort, PaginationSearch

E = TypeVar("E")
F = TypeVar("F")
O = TypeVar("O")
C = TypeVar("C")
T = TypeVar("T")


class PaginationUtils:
    def generate_paging_parameters(
        self,
        page: int,
        size: int,
        search: list[str] | None,
        sort: list[str] | None,
        find_all_query: F = None,
        order_by_query: O = None,
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
        entity: E,
        paging_options: Pagination,
        columns: list[str],
        search_all: str | None,
        columns_query: C,
        find_all_query: F | None = None,
    ) -> FindManyOptions:
        formatted_skip_take = self.format_skip_take_options(paging_options)

        paging_data = FindManyOptions(
            select=[],
            where=[],
            order_by=[],
            relations=[],
        )

        self.sort_data(paging_options, entity, paging_data)
        self.search_data(paging_options, entity, paging_data)
        self.search_all_data(entity, paging_data, search_all, find_all_query)
        self.select_columns(columns, columns_query, entity, paging_data)

        paging_data = {**paging_data, **formatted_skip_take}
        return paging_data

    @staticmethod
    def sort_data(paging_options: Pagination, entity: E, paging_data: FindManyOptions):
        if "sort" not in paging_options:
            return

        for sort_param in paging_options["sort"]:
            sort_obj = getattr(entity, sort_param["field"])
            sort_func = "asc" if sort_param.get("by") == "ASC" else "desc"
            paging_data["order_by"].append(getattr(sort_obj, sort_func)())

    @staticmethod
    def search_data(paging_options: Pagination, entity: E, paging_data: FindManyOptions):
        if "search" not in paging_options:
            return

        for search_param in paging_options["search"]:
            search_obj = getattr(entity, search_param["field"])
            paging_data["where"].append(
                cast_if(search_obj, String).ilike(f'%{search_param["value"]}%')
            )

    @staticmethod
    def search_all_data(
        entity: E,
        paging_data: FindManyOptions,
        search_all: str = None,
        find_all_query: F = None,
    ):
        if not search_all:
            return

        where_columns = find_all_query.__fields__ if find_all_query else get_columns(entity).keys()

        where_clauses = [
            cast(getattr(entity, column), String).ilike(f"%{search_all}%")
            for column in where_columns
        ]
        paging_data.setdefault("where", []).append(or_(*where_clauses))

    @staticmethod
    def select_columns(
        selected_columns: list[str],
        columns_query: C,
        entity: E,
        paging_options: FindManyOptions,
    ):
        if PaginationUtils.validate_columns(list(set(selected_columns)), columns_query):
            (
                paging_options,
                selected_columns,
            ) = PaginationUtils.generating_selected_relationships_and_columns(
                paging_options, list(set(selected_columns)), columns_query, entity
            )
        else:
            raise BadRequestException("Invalid columns")

    @staticmethod
    def format_skip_take_options(
        paging_options: Pagination,
    ) -> FindManyOptions:
        paging_data = FindManyOptions(
            skip=(paging_options["skip"] - 1) * paging_options["take"],
            take=paging_options["take"],
        )

        return paging_data

    @staticmethod
    def _remove_duplicate_params(params: list[str]) -> list[str]:
        return list(set(params))

    @staticmethod
    def _create_pagination_sort(sort_params: list[str]) -> list[PaginationSort]:
        pagination_sorts = []
        for sort_param in sort_params:
            sort_param_split = sort_param.split(":")
            pagination_sorts.append(
                PaginationSort(field=sort_param_split[0], by=sort_param_split[1])
            )
        return pagination_sorts

    @staticmethod
    def _create_pagination_search(search_params: list[str]) -> list[PaginationSearch]:
        pagination_search = []
        for search_param in search_params:
            search_param_split = search_param.split(":")
            pagination_search.append(
                PaginationSearch(field=search_param_split[0], value=search_param_split[1])
            )
        return pagination_search

    @staticmethod
    def _check_and_raise_for_invalid_sort_filters(
        pagination_sorts: list[PaginationSort], order_by_query: O = None
    ) -> None:
        if order_by_query and not PaginationUtils._is_valid_sort_params(
            pagination_sorts, order_by_query
        ):
            raise BadRequestException("Invalid sort filters")

    @staticmethod
    def _check_and_raise_for_invalid_search_filters(
        pagination_search: List[PaginationSearch], find_all_query: F = None
    ) -> None:
        if find_all_query and not PaginationUtils._is_valid_search_params(
            pagination_search, find_all_query
        ):
            raise BadRequestException("Invalid search filters")

    @staticmethod
    def _is_valid_sort_params(sort: List[PaginationSort], order_by_query_dto: O) -> bool:
        query_dto_fields = order_by_query_dto.__fields__

        is_valid_field = all(sort_param["field"] in query_dto_fields for sort_param in sort)
        is_valid_direction = all(sort_param["by"] in ["ASC", "DESC"] for sort_param in sort)

        return is_valid_field and is_valid_direction

    @staticmethod
    def _is_valid_search_params(search: List[PaginationSearch], find_all_query: F) -> bool:
        query_dto_fields = find_all_query.__fields__

        if not PaginationUtils.validate_required_search_filter(search, query_dto_fields):
            return False

        for search_param in search:
            if search_param["field"] not in query_dto_fields:
                return False

        return True

    @staticmethod
    def validate_required_search_filter(
        search: List[PaginationSearch], query_dto_fields: F
    ) -> bool:
        search_fields = [search_param["field"] for search_param in search]
        for field in query_dto_fields:
            if query_dto_fields[field].is_required() and field not in search_fields:
                return False

        return True

    @staticmethod
    def validate_columns(columns: List[str], columns_query_dto: C) -> bool:
        query_dto_fields = columns_query_dto.__fields__

        for column in columns:
            if column not in query_dto_fields:
                return False

        return True

    @staticmethod
    def generating_selected_relationships_and_columns(
        paging_options: FindManyOptions,
        selected_columns: List[str],
        columns_query_dto: C,
        entity: E,
    ) -> (FindManyOptions, List[str]):
        query_dto_fields = columns_query_dto.__fields__
        entity_relationships = inspect(inspect(entity).class_).relationships

        for field in query_dto_fields:
            if field in entity_relationships:
                if query_dto_fields[field].is_required() or field in selected_columns:
                    paging_options.setdefault("relations", []).append(field)
                    selected_columns.remove(field) if field in selected_columns else None
                    column_name = list(entity_relationships[field].local_columns)[0].name
                    selected_columns.append(getattr(entity, column_name))

            elif query_dto_fields[field].is_required() and field not in selected_columns:
                selected_columns.append(getattr(entity, field))

        if not paging_options.get("relations"):
            paging_options.pop("relations", None)

        paging_options["select"] = paging_options.get("select", []) + selected_columns
        if not paging_options.get("select"):
            paging_options.pop("select", None)

        return paging_options, selected_columns

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
