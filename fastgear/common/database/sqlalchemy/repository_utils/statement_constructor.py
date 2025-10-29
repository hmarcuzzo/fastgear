from typing import Any

from sqlalchemy import (
    BinaryExpression,
    Delete,
    Select,
    String,
    Update,
    asc,
    bindparam,
    delete,
    desc,
    inspect,
    or_,
    select,
    update,
)
from sqlalchemy.orm import load_only, selectinload
from sqlalchemy_utils import cast_if

from fastgear.types.delete_options import DeleteOptions
from fastgear.types.find_many_options import FindManyOptions
from fastgear.types.find_one_options import FindOneOptions
from fastgear.types.generic_types_var import EntityType
from fastgear.types.pagination import Pagination, PaginationSearch
from fastgear.types.update_options import UpdateOptions


class StatementConstructor:
    def __init__(self, entity: EntityType) -> None:
        self.entity = entity

    def build_select_statement(
        self,
        criteria: str | FindOneOptions | FindManyOptions | Pagination = None,
        new_entity: EntityType = None,
    ) -> Select:
        """Constructs and returns a SQLAlchemy Select statement based on the provided criteria and entity.

        Args:
            criteria (str | FindOneOptions | FindManyOptions, Pagination, optional): The filter criteria to build the select
                statement. It can be a string, an instance of FindOneOptions, an instance of FindManyOptions or Pagination.
                Defaults to None.
            new_entity (EntityType, optional): A new entity type to use for the select statement.
                If not provided, the existing entity type will be used. Defaults to None.

        Returns:
            Select: The constructed SQLAlchemy Select statement.

        """
        entity = new_entity if new_entity is not None else self.entity

        if isinstance(criteria, str):
            criteria = self.build_where_from_id(criteria, entity)

        statement = select(entity)

        return self._apply_select_options(statement, entity, criteria)

    def _apply_select_options(
        self,
        statement: Select,
        entity: EntityType,
        options_dict: FindOneOptions | FindManyOptions = None,
    ) -> Select:
        """Applies various options to the given SQLAlchemy Select statement based on the provided option's dictionary.

        Args:
            statement (Select): The initial SQLAlchemy Select statement to which options will be applied.
            entity (EntityType): The entity type associated with the select statement.
            options_dict (FindOneOptions | FindManyOptions, optional): A dictionary containing various options to be
                applied to the select statement. Defaults to None.

        Returns:
            Select: The modified SQLAlchemy Select statement with the applied options.

        """
        if not options_dict:
            return statement

        options_dict = self._fix_options_dict(options_dict)

        for key, value in options_dict.items():
            match key:
                case "select":
                    statement = statement.options(load_only(*value, raiseload=True))
                case "where":
                    statement = statement.where(*value)
                case "order_by":
                    statement = statement.order_by(*value)
                case "skip":
                    statement = statement.offset(value)
                case "take":
                    statement = statement.limit(value)
                case "relations":
                    statement = statement.options(
                        *[selectinload(getattr(entity, relation)) for relation in value]
                    )
                case "with_deleted":
                    statement = statement.execution_options(with_deleted=value)
                case _:
                    raise KeyError(f"Unknown option: {key} in FindOptions")

        return statement

    def build_update_statement(
        self,
        criteria: str | UpdateOptions = None,
        *,
        new_entity: EntityType = None,
        payload: dict[str, Any],
    ) -> Update:
        entity = new_entity if new_entity is not None else self.entity

        if isinstance(criteria, str):
            criteria = self.build_where_from_id(criteria, entity)

        diff_conditions = [
            getattr(entity, k).is_distinct_from(bindparam(f"cmp_{k}")) for k in payload
        ]

        criteria["where"].append(or_(*diff_conditions))  # Only update if values are different

        statement = update(entity)

        statement = self._apply_update_options(statement, criteria)
        return statement.values(**payload)

    def _apply_update_options(
        self,
        statement: Update,
        options_dict: UpdateOptions = None,
    ) -> Update:
        """Applies various options to the given SQLAlchemy Select statement based on the provided option's dictionary.

        Args:
            statement (Update): The initial SQLAlchemy Select statement to which options will be applied.
            options_dict (UpdateOptions, optional): A dictionary containing various options to be
                applied to the update statement. Defaults to None.

        Returns:
            Update: The modified SQLAlchemy Select statement with the applied options.
        """
        if not options_dict:
            return statement

        options_dict = self._fix_options_dict(options_dict)

        for key, value in options_dict.items():
            match key:
                case "where":
                    statement = statement.where(*value)
                case _:
                    raise KeyError(f"Unknown option: {key} in UpdateOptions")

        return statement

    def build_delete_statement(
        self,
        criteria: str | DeleteOptions = None,
        *,
        new_entity: EntityType = None,
    ) -> Update:
        entity = new_entity if new_entity is not None else self.entity

        if isinstance(criteria, str):
            criteria = self.build_where_from_id(criteria, entity)

        statement = delete(entity)

        return self._apply_delete_options(statement, criteria)

    def _apply_delete_options(
        self,
        statement: Delete,
        options_dict: DeleteOptions = None,
    ) -> Delete:
        """Applies various options to the given SQLAlchemy Select statement based on the provided option's dictionary.

        Args:
            statement (Delete): The initial SQLAlchemy Select statement to which options will be applied.
            options_dict (DeleteOptions, optional): A dictionary containing various options to be
                applied to the delete statement. Defaults to None.

        Returns:
            Delete: The modified SQLAlchemy Select statement with the applied options.
        """
        if not options_dict:
            return statement

        options_dict = self._fix_options_dict(options_dict)

        for key, value in options_dict.items():
            match key:
                case "where":
                    statement = statement.where(*value)
                case _:
                    raise KeyError(f"Unknown option: {key} in UpdateOptions")

        return statement

    @staticmethod
    def extract_from_mapping(field_mapping: dict, fields: list) -> list:
        """Extracts and returns a list of items from the field mapping based on the provided fields.

        Args:
            field_mapping (dict): A dictionary mapping fields to their corresponding items.
            fields (list): A list of fields to extract items for.

        Returns:
            list: A list of items extracted from the field mapping based on the provided fields.

        """
        return [
            item
            for field in fields
            for item in (
                field_mapping.get(field, [field])
                if isinstance(field_mapping.get(field, field), list)
                else [field_mapping.get(field, field)]
            )
        ]

    @staticmethod
    def _fix_options_dict(
        options_dict: FindOneOptions | FindManyOptions | UpdateOptions,
    ) -> FindOneOptions | FindManyOptions:
        """Ensures that specific attributes in the options dictionary are lists.

        Args:
            options_dict (FindOneOptions | FindManyOptions | UpdateOptions): The options dictionary to be fixed.

        Returns:
            FindOneOptions | FindManyOptions: The fixed options dictionary with specific attributes as lists.

        """
        for attribute in ["where", "order_by", "options"]:
            if attribute in options_dict and not isinstance(options_dict[attribute], list):
                options_dict[attribute] = [options_dict[attribute]]

        return options_dict

    @staticmethod
    def build_where_from_id(criteria: str, entity: EntityType) -> FindOneOptions | UpdateOptions:
        """Generates a FindOneOptions or UpdateOptions dictionary based on the provided criteria and entity.

        Args:
            criteria (str): The criteria to filter the entity. Typically, this is the primary key value.
            entity (EntityType): The entity type for which the options dictionary is being generated.

        Returns:
            FindOneOptions | UpdateOptions: A dictionary containing the 'where' clause for filtering the entity.

        """
        return {"where": [inspect(entity).primary_key[0] == criteria]}

    def build_options(self, pagination: Pagination) -> FindOneOptions | FindManyOptions:
        find_options = {
            "skip": pagination.skip,
            "take": pagination.take,
            "where": [],
            "order_by": [],
            "select": [],
            "relations": [],
        }

        def _make_clause(item: PaginationSearch) -> BinaryExpression:
            field = getattr(self.entity, item.get("field"), item.get("field"))
            value = item.get("value")
            return cast_if(field, String).ilike(f"%{value}%")

        search = getattr(pagination, "search", [])
        where = find_options.get("where", [])
        for param in search:
            items = param if isinstance(param, list) else [param]
            clauses = [_make_clause(it) for it in items]

            if not clauses:
                continue

            where.append(or_(*clauses) if len(clauses) > 1 else clauses[0])

        sort = getattr(pagination, "sort", [])
        order_by = find_options.get("order_by", [])
        for param in sort:
            field = getattr(self.entity, param.get("field"), param.get("field"))
            order_by.append(asc(field) if param.get("by") == "ASC" else desc(field))

        entity_relationships = inspect(self.entity).relationships
        relations = find_options.get("relations", [])
        select_options = find_options.get("select", [])
        for field in getattr(pagination, "columns", []):
            if field in entity_relationships:
                relations.append(field)
            else:
                select_options.append(getattr(self.entity, field, field))

        return find_options
