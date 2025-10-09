from sqlalchemy import BinaryExpression, Select, String, asc, desc, inspect, or_, select
from sqlalchemy.orm import load_only, selectinload
from sqlalchemy_utils import cast_if

from fastgear.types.find_many_options import FindManyOptions
from fastgear.types.find_one_options import FindOneOptions
from fastgear.types.generic_types_var import EntityType
from fastgear.types.pagination import Pagination, PaginationSearch


class SelectConstructor:
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
        entity = new_entity or self.entity

        if isinstance(criteria, str):
            criteria = self.__generate_find_one_options_dict(criteria, entity)

        select_statement = select(entity)

        return self.__apply_options(select_statement, entity, criteria)

    def __apply_options(
        self,
        select_statement: Select,
        entity: EntityType,
        options_dict: FindOneOptions | FindManyOptions = None,
    ) -> Select:
        """Applies various options to the given SQLAlchemy Select statement based on the provided option's dictionary.

        Args:
            select_statement (Select): The initial SQLAlchemy Select statement to which options will be applied.
            entity (EntityType): The entity type associated with the select statement.
            options_dict (FindOneOptions | FindManyOptions, optional): A dictionary containing various options to be
                applied to the select statement. Defaults to None.

        Returns:
            Select: The modified SQLAlchemy Select statement with the applied options.

        """
        if not options_dict:
            return select_statement

        options_dict = self.__fix_options_dict(options_dict)

        for key, item in options_dict.items():
            match key:
                case "select":
                    select_statement = select_statement.options(load_only(*item, raiseload=True))
                case "where":
                    select_statement = select_statement.where(*item)
                case "order_by":
                    select_statement = select_statement.order_by(*item)
                case "skip":
                    select_statement = select_statement.offset(item)
                case "take":
                    select_statement = select_statement.limit(item)
                case "relations":
                    select_statement = select_statement.options(
                        *[selectinload(getattr(entity, relation)) for relation in item]
                    )
                case "with_deleted":
                    select_statement = select_statement.execution_options(with_deleted=item)
                case _:
                    raise KeyError(f"Unknown option: {key} in FindOptions")

        return select_statement

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
    def __fix_options_dict(
        options_dict: FindOneOptions | FindManyOptions,
    ) -> FindOneOptions | FindManyOptions:
        """Ensures that specific attributes in the options dictionary are lists.

        Args:
            options_dict (FindOneOptions | FindManyOptions): The options dictionary to be fixed.

        Returns:
            FindOneOptions | FindManyOptions: The fixed options dictionary with specific attributes as lists.

        """
        for attribute in ["where", "order_by", "options"]:
            if attribute in options_dict and not isinstance(options_dict[attribute], list):
                options_dict[attribute] = [options_dict[attribute]]

        return options_dict

    @staticmethod
    def __generate_find_one_options_dict(criteria: str, entity: EntityType) -> FindOneOptions:
        """Generates a FindOneOptions dictionary based on the provided criteria and entity.

        Args:
            criteria (str): The criteria to filter the entity. Typically, this is the primary key value.
            entity (EntityType): The entity type for which the options dictionary is being generated.

        Returns:
            FindOneOptions: A dictionary with a 'where' clause that filters the entity based on the primary key.

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
