from sqlalchemy import Select, inspect, select
from sqlalchemy.orm import load_only, selectinload

from fastutils_hmarcuzzo.types.find_many_options import FindManyOptions
from fastutils_hmarcuzzo.types.find_one_options import FindOneOptions
from fastutils_hmarcuzzo.types.generic_types_var import EntityType


class SelectConstructor:
    def __init__(self, entity: EntityType) -> None:
        self.entity = entity

    def build_select_statement(
        self, criteria: str | FindOneOptions | FindManyOptions = None, new_entity: EntityType = None,
    ) -> Select:
        """Constructs and returns a SQLAlchemy Select statement based on the provided criteria and entity.

        Args:
            criteria (str | FindOneOptions | FindManyOptions, optional): The filter criteria to build the select
                statement. It can be a string, an instance of FindOneOptions, or an instance of FindManyOptions.
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

        for key in options_dict:
            match key:
                case "select":
                    select_statement = select_statement.options(
                        load_only(*options_dict[key], raiseload=True),
                    )
                case "where":
                    select_statement = select_statement.where(*options_dict[key])
                case "order_by":
                    select_statement = select_statement.order_by(*options_dict[key])
                case "skip":
                    select_statement = select_statement.offset(options_dict[key])
                case "take":
                    select_statement = select_statement.limit(options_dict[key])
                case "relations":
                    select_statement = select_statement.options(
                        *[selectinload(getattr(entity, relation)) for relation in options_dict[key]],
                    )
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
