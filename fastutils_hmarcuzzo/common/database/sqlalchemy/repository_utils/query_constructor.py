from typing import TypeVar

from sqlalchemy import inspect
from sqlalchemy.orm import Session, Query, load_only, lazyload

from fastutils_hmarcuzzo.types.find_many_options import FindManyOptions
from fastutils_hmarcuzzo.types.find_one_options import FindOneOptions

T = TypeVar("T")
E = TypeVar("E")


class QueryConstructor:
    def __init__(self, entity: T):
        self.entity = entity

    def build_query(
        self,
        db: Session,
        criteria: str | FindOneOptions | FindManyOptions = None,
        entity: E = None,
    ) -> Query:
        entity = entity or self.entity

        if isinstance(criteria, str):
            criteria = self.__generate_find_one_options_dict(criteria, entity)

        query = db.query(entity)

        return self.__apply_options(query, entity, criteria)

    def __apply_options(
        self,
        query: Query,
        entity: T | E,
        options_dict: FindOneOptions | FindManyOptions = None,
    ) -> Query:
        if not options_dict:
            return query

        options_dict = self.__fix_options_dict(options_dict)
        query = query.enable_assertions(False)

        for key in options_dict.keys():
            if key == "select":
                query = query.options(load_only(*options_dict[key]))
            elif key == "where":
                query = query.where(*options_dict[key])
            elif key == "order_by":
                query = query.order_by(*options_dict[key])
            elif key == "skip":
                query = query.offset(options_dict[key])
            elif key == "take":
                query = query.limit(options_dict[key])
            elif key == "relations":
                query = query.options(
                    *[lazyload(getattr(entity, relation)) for relation in options_dict[key]]
                )
            else:
                raise KeyError(f"Unknown option: {key} in FindOptions")

        return query

    @staticmethod
    def __fix_options_dict(
        options_dict: FindOneOptions | FindManyOptions,
    ) -> FindOneOptions | FindManyOptions:
        for attribute in ["where", "order_by", "options"]:
            if attribute in options_dict and not isinstance(options_dict[attribute], list):
                options_dict[attribute] = [options_dict[attribute]]

        return options_dict

    @staticmethod
    def __generate_find_one_options_dict(criteria: str, entity: T | E) -> FindOneOptions:
        return {"where": [inspect(entity).primary_key[0] == criteria]}
