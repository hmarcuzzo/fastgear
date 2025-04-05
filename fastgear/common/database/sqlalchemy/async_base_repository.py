import asyncio
from collections.abc import Sequence
from functools import singledispatchmethod

from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.sql.dml import Delete, ReturningDelete

from fastgear.common.database.abstract_repository import AbstractRepository
from fastgear.common.database.sqlalchemy.repository_utils.inject_db_parameter_decorator import (
    inject_db_parameter_decorator,
)
from fastgear.common.database.sqlalchemy.session import AsyncSessionType
from fastgear.types.delete_result import DeleteResult
from fastgear.types.find_many_options import FindManyOptions
from fastgear.types.find_one_options import FindOneOptions
from fastgear.types.generic_types_var import EntityType
from fastgear.types.http_exceptions import NotFoundException
from fastgear.types.update_result import UpdateResult


@inject_db_parameter_decorator
class AsyncBaseRepository(AbstractRepository[EntityType]):
    """Asynchronous base repository class for handling database operations for a specific entity type.

    This class provides methods for creating, reading, updating, and deleting records in the database.
    It uses SQLAlchemy for database interactions and Pydantic for data validation and serialization.

    Args:
        entity (type[EntityType]): The entity type that this repository will manage.

    """

    def __init__(self, entity: type[EntityType]) -> None:
        super().__init__(entity)

    async def create(
        self, new_record: EntityType | BaseModel, db: AsyncSessionType = None
    ) -> EntityType:
        """Creates a new record in the database.

        Args:
            new_record (EntityType | BaseModel): The new record to be created. It can be an instance of EntityType or
                BaseModel.
            db (AsyncSessionType, optional): The database session. Defaults to None.

        Returns:
            EntityType: The created record.

        """
        return (await self.create_all([new_record], db))[0]

    async def create_all(
        self, new_records: list[EntityType | BaseModel], db: AsyncSessionType = None
    ) -> list[EntityType]:
        """Creates multiple new records in the database.

        Args:
            new_records (List[EntityType | BaseModel]): A list of new records to be created. Each record can be an
                instance of EntityType or BaseModel.
            db (AsyncSessionType, optional): The database session. Defaults to None.

        Returns:
            List[EntityType]: A list of the created records.

        """
        for index, record in enumerate(new_records):
            if isinstance(record, BaseModel):
                model_data = record.model_dump(exclude_unset=True)
                new_records[index] = self.entity(**model_data)

        db.add_all(new_records)
        await db.flush()
        return new_records

    @staticmethod
    async def save(
        new_record: EntityType | list[EntityType] = None, db: AsyncSessionType = None
    ) -> EntityType | list[EntityType] | None:
        """Saves the given record(s) to the database by committing or flushing the session.

        Args:
            new_record (EntityType | List[EntityType], optional): The record(s) to be saved. If provided, the record(s)
                will be refreshed after saving. Defaults to None.
            db (AsyncSessionType, optional): The database session. Defaults to None.

        Returns:
            EntityType | List[EntityType] | None: The saved record(s) or None if no record was provided.

        """
        await AsyncBaseRepository.commit_or_flush(db)

        if new_record:
            await AsyncBaseRepository.refresh_record(new_record, db)
        return new_record

    @staticmethod
    async def commit_or_flush(db: AsyncSessionType = None) -> None:
        """Commits the current transaction if not in a nested transaction, otherwise flushes the session.

        Args:
            db (AsyncSessionType, optional): The database session. Defaults to None.

        Returns:
            None
        """
        await db.flush() if db.in_nested_transaction() else await db.commit()

    @staticmethod
    async def refresh_record(
        new_record: EntityType | list[EntityType], db: AsyncSessionType = None
    ) -> EntityType | list[EntityType]:
        """Refreshes the given record(s) in the database session.

        Args:
            new_record (EntityType | List[EntityType]): The record(s) to be refreshed. It can be a single instance or
                a list of instances.
            db (AsyncSessionType, optional): The database session. Defaults to None.

        Returns:
            EntityType | List[EntityType]: The refreshed record(s).

        """
        await asyncio.gather(*(db.refresh(entity) for entity in new_record)) if isinstance(
            new_record, list
        ) else await db.refresh(new_record)
        return new_record

    async def find_one(
        self, search_filter: str | FindOneOptions, db: AsyncSessionType = None
    ) -> EntityType | None:
        """Finds a single record in the database that matches the given search filter.

        Args:
            search_filter (str | FindOneOptions): The search filter to apply. It can be a string or an instance of
                FindOneOptions.
            db (AsyncSessionType, optional): The database session. Defaults to None.

        Returns:
            EntityType | None: The found record or None if no record matches the search filter.

        """
        select_statement = self.select_constructor.build_select_statement(search_filter)
        result = (await db.execute(select_statement)).first()

        return result[0] if result else None

    async def find_one_or_fail(
        self, search_filter: str | FindOneOptions, db: AsyncSessionType = None
    ) -> EntityType:
        """Finds a single record in the database that matches the given search filter or raises an exception if no
        record is found.

        Args:
            search_filter (str | FindOneOptions): The search filter to apply. It can be a string or an instance
                of FindOneOptions.
            db (AsyncSessionType, optional): The database session. Defaults to None.

        Returns:
            EntityType: The found record.

        Raises:
            NotFoundException: If no record matches the search filter.

        """
        select_statement = self.select_constructor.build_select_statement(search_filter)
        try:
            result = (await db.execute(select_statement)).one()[0]
        except NoResultFound:
            entity_name = self.entity.__name__
            message = f'Could not find any entity of type "{entity_name}" that matches with the search filter'
            self.logger.debug(message)
            raise NotFoundException(message, [entity_name])

        return result

    @singledispatchmethod
    async def find(
        self, stmt_or_filter: FindManyOptions | Select = None, db: AsyncSessionType = None
    ) -> Sequence[EntityType]:
        """Finds multiple records in the database that match the given statement or filter.

        Args:
            stmt_or_filter (FindManyOptions | Select, optional): The statement or filter to apply. It can be an instance
                of FindManyOptions or a SQLAlchemy Select statement. Defaults to None.
            db (AsyncSessionType, optional): The database session. Defaults to None.

        Returns:
            Sequence[EntityType]: A sequence of the found records.

        """
        message = f"Unsupported type: {type(stmt_or_filter)}"
        self.logger.debug(message)
        raise NotImplementedError(message)

    @find.register
    async def _(
        self, options: FindManyOptions | dict | None, db: AsyncSessionType = None
    ) -> Sequence[EntityType]:
        """Implementation when stmt_or_filter is an instance of FindManyOptions."""
        select_statement = self.select_constructor.build_select_statement(options)
        return await self.find(select_statement, db=db)  # Call the method registered for Select

    @find.register
    async def _(self, select_stmt: Select, db: AsyncSessionType = None) -> Sequence[EntityType]:
        """Implementation when stmt_or_filter is an instance of Select."""
        return (await db.execute(select_stmt)).scalars().all()

    @singledispatchmethod
    async def count(
        self, stmt_or_filter: FindManyOptions | Select = None, db: AsyncSessionType = None
    ) -> int:
        """Counts the number of records in the database that match the given statement or filter.

        Args:
            stmt_or_filter (FindManyOptions | Select, optional): The statement or filter to apply. It can be an
                instance of FindManyOptions or a SQLAlchemy Select statement. Defaults to None.
            db (AsyncSessionType, optional): The database session. Defaults to None.

        Returns:
            int: The count of records that match the given statement or filter.

        """
        message = f"Unsupported type: {type(stmt_or_filter)}"
        self.logger.debug(message)
        raise NotImplementedError(message)

    @count.register
    async def _(self, options: FindManyOptions | dict | None, db: AsyncSessionType = None) -> int:
        """Implementation when stmt_or_filter is an instance of FindManyOptions."""
        select_statement = self.select_constructor.build_select_statement(options)
        return await self.count(select_statement, db=db)

    @count.register
    async def _(self, select_stmt: Select, db: AsyncSessionType = None) -> int:
        """Implementation when stmt_or_filter is an instance of Select."""
        return (
            await db.execute(
                select(func.count("*")).select_from(select_stmt.offset(None).limit(None).subquery())
            )
        ).scalar()

    async def find_and_count(
        self, search_filter: FindManyOptions = None, db: AsyncSessionType = None
    ) -> tuple[Sequence[EntityType], int]:
        """Finds multiple records in the database that match the given search filter and counts the total number of
        matching records.

        Args:
            search_filter (FindManyOptions, optional): The search filter to apply. It can be an instance of
            FindManyOptions. Defaults to None.
            db (AsyncSessionType, optional): The database session. Defaults to None.

        Returns:
            Tuple[Sequence[EntityType], int]: A tuple containing a sequence of the found records and the count of
                matching records.

        """
        select_statement = self.select_constructor.build_select_statement(search_filter)
        count = await self.count(select_statement, db)
        result = await self.find(select_statement, db)

        return result, count

    async def update(
        self,
        search_filter: str | FindOneOptions,
        model_data: BaseModel | dict,
        db: AsyncSessionType = None,
    ) -> UpdateResult:
        """Updates a record in the database that matches the given search filter with the provided model data.

        Args:
            search_filter (str | FindOneOptions): The search filter to apply. It can be a string or an instance of
                FindOneOptions.
            model_data (BaseModel | dict): The data to update the record with. It can be an instance of BaseModel or
                a dictionary.
            db (AsyncSessionType, optional): The database session. Defaults to None.

        Returns:
            UpdateResult: The result of the update operation, including the updated record, the number of affected
                records, and any generated maps.

        """
        record = await self.find_one_or_fail(search_filter, db)

        if isinstance(model_data, BaseModel):
            model_data = model_data.model_dump(exclude_unset=True)

        changes_made = False
        for key, value in model_data.items():
            current_value = getattr(record, key, None)
            if current_value != value:
                setattr(record, key, value)
                changes_made = True

        if changes_made:
            await self.commit_or_flush(db)
            await self.refresh_record(record, db)

        return UpdateResult(
            raw=[record] if changes_made else [],
            affected=1 if changes_made else 0,
            generated_maps=[],
        )

    async def delete(
        self, delete_statement: str | FindOneOptions | ReturningDelete, db: AsyncSessionType = None
    ) -> DeleteResult:
        """Deletes a record in the database that matches the given delete statement.

        Args:
            delete_statement (str | FindOneOptions | ReturningDelete): The delete statement to apply. It can be a
                string, an instance of FindOneOptions, or a SQLAlchemy ReturningDelete statement.
            db (AsyncSessionType, optional): The database session. Defaults to None.

        Returns:
            DeleteResult: The result of the delete operation, including the raw result and the number of affected
                records.

        """
        if isinstance(delete_statement, Delete):
            raw = (await db.execute(delete_statement)).all()
        else:
            record = await self.find_one_or_fail(delete_statement, db)
            await db.delete(record)
            raw = [record.id]

        await self.commit_or_flush(db)
        return DeleteResult(raw=raw, affected=len(raw))
