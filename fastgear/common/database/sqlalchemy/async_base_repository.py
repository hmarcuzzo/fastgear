from collections.abc import Sequence
from functools import singledispatchmethod

from pydantic import BaseModel
from sqlalchemy import (
    Select,
    func,
    inspect,
    literal_column,
    select,
)
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.sql.dml import Delete, ReturningDelete

from fastgear.common.database.abstract_repository import AbstractRepository
from fastgear.common.database.sqlalchemy.repository_utils.inject_db_parameter_decorator import (
    inject_db_parameter_decorator,
)
from fastgear.common.database.sqlalchemy.session import AsyncSessionType
from fastgear.types.delete_options import DeleteOptions
from fastgear.types.delete_result import DeleteResult
from fastgear.types.find_many_options import FindManyOptions
from fastgear.types.find_one_options import FindOneOptions
from fastgear.types.generic_types_var import EntityType
from fastgear.types.http_exceptions import NotFoundException
from fastgear.types.pagination import Pagination
from fastgear.types.update_options import UpdateOptions
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

        items: list[EntityType] = []
        for record in new_records:
            item = record
            if isinstance(record, BaseModel):
                item = self.entity(**record.model_dump(exclude_unset=True))
            items.append(item)

        db.add_all(items)
        await db.flush()
        return items

    @staticmethod
    async def save(db: AsyncSessionType = None) -> None:
        """Saves the current transaction in the database session.

        Args:
            db (AsyncSessionType, optional): The database session. Defaults to None.

        Returns:
            None.

        """
        await db.flush() if db.in_nested_transaction() else await db.commit()

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
        select_statement = self.statement_constructor.build_select_statement(search_filter).limit(1)
        result = (await db.execute(select_statement)).scalars().first()

        return result if result else None

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
        select_statement = self.statement_constructor.build_select_statement(search_filter).limit(2)
        try:
            return (await db.execute(select_statement)).scalar_one()

        except NoResultFound:
            entity_name = self.entity.__name__
            message = f'Could not find any entity of type "{entity_name}" that matches with the search filter'
            self.logger.debug(message)
            raise NotFoundException(message, [entity_name])

        except MultipleResultsFound:
            entity_name = self.entity.__name__
            message = (
                f'Multiple entities of type "{entity_name}" found that match with the search filter'
            )
            self.logger.debug(message)
            raise NotFoundException(message, [entity_name])

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
        select_statement = self.statement_constructor.build_select_statement(options)
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
        select_statement = self.statement_constructor.build_select_statement(options)
        return await self.count(select_statement, db=db)

    @count.register
    async def _(self, select_stmt: Select, db: AsyncSessionType = None) -> int:
        """Implementation when stmt_or_filter is an instance of Select."""
        stmt = select(func.count()).select_from(
            select_stmt.limit(None)
            .offset(None)
            .order_by(None)
            .with_only_columns(literal_column("1"), maintain_column_froms=True)
            .subquery()
        )
        return await db.scalar(stmt)

    @singledispatchmethod
    async def find_and_count(
        self, search_filter: FindManyOptions | Pagination = None, db: AsyncSessionType = None
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
        message = f"Unsupported type: {type(search_filter)}"
        self.logger.debug(message)
        raise NotImplementedError(message)

    @find_and_count.register
    async def _(
        self, search_filter: Pagination, db: AsyncSessionType = None
    ) -> tuple[Sequence[EntityType], int]:
        """Implementation when search_filter is an instance of Pagination."""
        find_many_options = self.statement_constructor.build_options(search_filter)
        return await self.find_and_count(find_many_options, db)

    @find_and_count.register
    async def _(
        self, search_filter: FindManyOptions | dict | None, db: AsyncSessionType = None
    ) -> tuple[Sequence[EntityType], int]:
        """Implementation when search_filter is an instance of FindManyOptions."""
        select_statement = self.statement_constructor.build_select_statement(search_filter)
        count = await self.count(select_statement, db)
        result = await self.find(select_statement, db)

        return result, count

    async def update(
        self,
        update_filter: str | UpdateOptions,
        model_data: BaseModel | dict,
        db: AsyncSessionType = None,
    ) -> UpdateResult:
        """Updates a record in the database that matches the given search filter with the provided model data.

        Args:
            update_filter (str | UpdateOptions): The search filter to apply. It can be a string or an instance of
                UpdateOptions.
            model_data (BaseModel | dict): The data to update the record with. It can be an instance of BaseModel or
                a dictionary.
            db (AsyncSessionType, optional): The database session. Defaults to None.

        Returns:
            UpdateResult: The result of the update operation, including the updated record, the number of affected
                records, and any generated maps.

        """
        if isinstance(model_data, BaseModel):
            model_data = model_data.model_dump(exclude_unset=True)

        mapper = inspect(self.entity)
        column_keys = {a.key for a in mapper.attrs if hasattr(a, "columns")}
        payload = {k: v for k, v in model_data.items() if k in column_keys}

        if not payload:
            return UpdateResult(raw=[], affected=0, generated_maps=[])

        stmt = self.statement_constructor.build_update_statement(
            update_filter, payload=payload
        ).returning(self.entity)

        cmp_params = {f"cmp_{k}": v for k, v in payload.items()}
        params = {**payload, **cmp_params}
        res = await db.execute(stmt, params)

        await self.save(db)

        objs = res.scalars().all()
        affected = len(objs)
        return UpdateResult(raw=objs, affected=affected, generated_maps=[])

    async def delete(
        self, delete_statement: str | DeleteOptions | ReturningDelete, db: AsyncSessionType = None
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
            res = await db.execute(delete_statement)
            objs = res.all()
        else:
            stmt = self.statement_constructor.build_delete_statement(delete_statement).returning(
                self.entity
            )
            res = await db.execute(stmt)
            objs = res.scalars().all()

        await self.save(db)

        affected = len(objs)
        return DeleteResult(raw=objs, affected=affected)

    async def soft_delete(
        self, update_filter: str | UpdateOptions, db: AsyncSessionType = None
    ) -> UpdateResult:
        try:
            async with db.begin_nested():
                response = await db.run_sync(
                    lambda sync_db: self.repo_utils.soft_delete_cascade_from_parent(
                        self.entity,
                        update_filter=update_filter,
                        db=sync_db,
                    )
                )

            await self.save(db)
            return response

        except Exception as e:
            raise e
