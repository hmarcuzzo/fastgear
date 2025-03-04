from collections.abc import Sequence
from functools import singledispatchmethod

from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session, SessionTransaction
from sqlalchemy.sql.dml import Delete, ReturningDelete

from fastutils_hmarcuzzo.common.database.abstract_repository import AbstractRepository
from fastutils_hmarcuzzo.common.database.sqlalchemy.repository_utils.base_repository_utils import (
    BaseRepositoryUtils,
)
from fastutils_hmarcuzzo.common.database.sqlalchemy.repository_utils.inject_db_parameter_decorator import (
    inject_db_parameter_decorator,
)
from fastutils_hmarcuzzo.common.database.sqlalchemy.repository_utils.select_constructor import (
    SelectConstructor,
)
from fastutils_hmarcuzzo.types.delete_result import DeleteResult
from fastutils_hmarcuzzo.types.find_many_options import FindManyOptions
from fastutils_hmarcuzzo.types.find_one_options import FindOneOptions
from fastutils_hmarcuzzo.types.generic_types_var import EntityType
from fastutils_hmarcuzzo.types.http_exceptions import NotFoundException
from fastutils_hmarcuzzo.types.update_result import UpdateResult

SessionType = Session | SessionTransaction


@inject_db_parameter_decorator
class BaseRepository(AbstractRepository[EntityType]):
    """Base repository class for handling database operations for a specific entity type.

    This class provides methods for creating, reading, updating, and deleting records in the
        database.
    It uses SQLAlchemy for database interactions and Pydantic for data validation and serialization.

    Args:
        entity (type[EntityType]): The entity type that this repository will manage.

    """

    def __init__(self, entity: type[EntityType]) -> None:
        super().__init__(entity)
        self.select_constructor = SelectConstructor(entity)
        self.repo_utils = BaseRepositoryUtils()

    def create(self, new_record: EntityType | BaseModel, db: SessionType = None) -> EntityType:
        """Creates a new record in the database.

        Args:
            new_record (EntityType | BaseModel): The new record to be created. It can be an
                instance of EntityType or BaseModel.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            EntityType: The created record.

        """
        return (self.create_all([new_record], db))[0]

    def create_all(
        self, new_records: list[EntityType | BaseModel], db: SessionType = None,
    ) -> list[EntityType]:
        """Creates multiple new records in the database.

        Args:
            new_records (List[EntityType | BaseModel]): A list of new records to be created.
                Each record can be an instance of EntityType or BaseModel.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            List[EntityType]: A list of the created records.

        """
        for index, record in enumerate(new_records):
            if isinstance(record, BaseModel):
                model_data = record.model_dump(exclude_unset=True)
                new_records[index] = self.entity(**model_data)

        db.add_all(new_records)
        db.flush()
        return new_records

    def save(
        self, new_record: EntityType | list[EntityType] = None, db: SessionType = None,
    ) -> EntityType | list[EntityType] | None:
        """Saves the given record(s) to the database by committing or flushing the session.

        Args:
            new_record (EntityType | List[EntityType], optional): The record(s) to be saved.
                If provided, the record(s) will be refreshed after saving. Defaults to None.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            EntityType | List[EntityType] | None: The saved record(s) or None if no record
                was provided.

        """
        self.commit_or_flush(db)

        if new_record:
            self.refresh_record(new_record, db)
        return new_record

    @staticmethod
    def commit_or_flush(db: SessionType = None) -> None:
        """Commits the current transaction if not in a nested transaction, otherwise flushes
            the session.

        Args:
            db (SessionType, optional): The database session. Defaults to None.

        """
        db.flush() if db.in_nested_transaction() else db.commit()

    @staticmethod
    def refresh_record(
        new_record: EntityType | list[EntityType], db: SessionType = None,
    ) -> EntityType | list[EntityType]:
        """Refreshes the state of the record(s) from the database.

        Args:
            new_record (EntityType | List[EntityType]): The record(s) to be refreshed.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            EntityType | List[EntityType]: The refreshed record(s).

        """
        (
            db.refresh(new_record)
            if not isinstance(new_record, list)
            else (db.refresh(_entity) for _entity in new_record)
        )
        return new_record

    def find_one(
        self, search_filter: str | FindOneOptions, db: SessionType = None,
    ) -> EntityType | None:
        """Finds a single record that matches the given search filter.

        Args:
            search_filter (str | FindOneOptions): The filter criteria to search for the record.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            EntityType | None: The found record or None if no record matches the search filter.

        """
        select_statement = self.select_constructor.build_select_statement(search_filter)
        result = db.execute(select_statement).first()

        return result[0] if result else None

    def find_one_or_fail(
        self, search_filter: str | FindOneOptions, db: SessionType = None,
    ) -> EntityType:
        """Finds a single record that matches the given search filter or raises an exception if
            no record is found.

        Args:
            search_filter (str | FindOneOptions): The filter criteria to search for the record.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            EntityType: The found record.

        Raises:
            NotFoundException: If no record matches the search filter.

        """
        select_statement = self.select_constructor.build_select_statement(search_filter)
        try:
            result = db.execute(select_statement).one()[0]
        except NoResultFound:
            entity_name = self.entity.__name__
            message = (
                f'Could not find any entity of type "{entity_name}" that matches with the '
                f"search filter"
            )
            raise NotFoundException(message, [entity_name])

        return result

    @singledispatchmethod
    def find(
        self, stmt_or_filter: FindManyOptions | Select = None, db: SessionType = None,
    ) -> Sequence[EntityType]:
        """Finds multiple records that match the given filter criteria or SQL statement.

        Args:
            stmt_or_filter (FindManyOptions | Select, optional): The filter criteria or SQL
                statement to search for the records. Defaults to None.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            Sequence[EntityType]: A sequence of found records.

        """
        raise NotImplementedError(f"Unsupported type: {type(stmt_or_filter)}")

    @find.register
    def _(
        self, options: FindManyOptions | dict | None, db: SessionType = None,
    ) -> Sequence[EntityType]:
        """Implementation when stmt_or_filter is an instance of FindManyOptions."""
        select_statement = self.select_constructor.build_select_statement(options)
        return self.find(select_statement, db=db)  # Call the method registered for Select

    @find.register
    def _(self, select_stmt: Select, db: SessionType = None) -> Sequence[EntityType]:
        """Implementation when stmt_or_filter is an instance of Select."""
        return db.execute(select_stmt).scalars().all()

    @singledispatchmethod
    def count(self, stmt_or_filter: FindManyOptions | Select = None, db: SessionType = None) -> int:
        """Counts the number of records that match the given filter criteria or SQL statement.

        Args:
            stmt_or_filter (FindManyOptions | Select, optional): The filter criteria or SQL
                statement to count the records. Defaults to None.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            int: The count of records that match the filter criteria or SQL statement.

        """
        raise NotImplementedError(f"Unsupported type: {type(stmt_or_filter)}")

    @count.register
    def _(self, options: FindManyOptions | dict | None, db: SessionType = None) -> int:
        """Implementation when stmt_or_filter is an instance of FindManyOptions."""
        select_statement = self.select_constructor.build_select_statement(options)
        return self.count(select_statement, db=db)

    @count.register
    def _(self, select_stmt: Select, db: SessionType = None) -> int:
        """Implementation when stmt_or_filter is an instance of Select."""
        return db.execute(
            select(func.count("*")).select_from(select_stmt.offset(None).limit(None).subquery()),
        ).scalar()

    def find_and_count(
        self, search_filter: FindManyOptions = None, db: SessionType = None,
    ) -> tuple[Sequence[EntityType], int]:
        """Finds multiple records that match the given filter criteria and counts the total number
            of matching records.

        Args:
            search_filter (FindManyOptions, optional): The filter criteria to search for the
                records. Defaults to None.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            Tuple[Sequence[EntityType], int]: A tuple containing a sequence of found records and
                the count of matching records.

        """
        select_statement = self.select_constructor.build_select_statement(search_filter)
        count = self.count(select_statement, db)
        result = self.find(select_statement, db)

        return result, count

    def update(
        self,
        search_filter: str | FindOneOptions,
        model_data: BaseModel | dict,
        db: SessionType = None,
    ) -> UpdateResult:
        """Updates a record that matches the given search filter with the provided model data.

        Args:
            search_filter (str | FindOneOptions): The filter criteria to search for the record
                to be updated.
            model_data (BaseModel | dict): The data to update the record with.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            UpdateResult: The result of the update operation, including the updated record, the
                number of affected records, and any generated maps.

        """
        record = self.find_one_or_fail(search_filter, db)

        if isinstance(model_data, BaseModel):
            model_data = model_data.model_dump(exclude_unset=True)

        changes_made = False
        for key, value in model_data.items():
            current_value = getattr(record, key, None)
            if current_value != value:
                setattr(record, key, value)
                changes_made = True

        if changes_made:
            self.commit_or_flush(db)

        return UpdateResult(
            raw=[record] if changes_made else [],
            affected=1 if changes_made else 0,
            generated_maps=[],
        )

    def delete(
        self, delete_statement: str | FindOneOptions | ReturningDelete, db: SessionType = None,
    ) -> DeleteResult:
        """Deletes a record that matches the given delete statement or filter criteria.

        Args:
            delete_statement (str | FindOneOptions | ReturningDelete): The delete statement or
                filter criteria to find the record to be deleted.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            DeleteResult: The result of the delete operation, including the raw data of deleted
                records and the number of affected records.

        """
        if isinstance(delete_statement, Delete):
            raw = db.execute(delete_statement).all()
        else:
            record = self.find_one_or_fail(delete_statement, db)
            db.delete(record)
            raw = [record.id]

        self.commit_or_flush(db)
        return DeleteResult(raw=raw, affected=len(raw))
