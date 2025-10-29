from collections.abc import Sequence
from functools import singledispatchmethod

from pydantic import BaseModel
from sqlalchemy import Select, func, inspect, literal_column, select
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.sql.dml import Delete, ReturningDelete

from fastgear.common.database.abstract_repository import AbstractRepository
from fastgear.common.database.sqlalchemy.session import SyncSessionType
from fastgear.types.delete_result import DeleteResult
from fastgear.types.find_many_options import FindManyOptions
from fastgear.types.find_one_options import FindOneOptions
from fastgear.types.generic_types_var import EntityType
from fastgear.types.http_exceptions import NotFoundException
from fastgear.types.pagination import Pagination
from fastgear.types.update_options import UpdateOptions
from fastgear.types.update_result import UpdateResult


class SyncBaseRepository(AbstractRepository[EntityType]):
    """Base repository class for handling database operations for a specific entity type.

    This class provides methods for creating, reading, updating, and deleting records in the
        database.
    It uses SQLAlchemy for database interactions and Pydantic for data validation and serialization.

    Args:
        entity (type[EntityType]): The entity type that this repository will manage.

    """

    def __init__(self, entity: type[EntityType]) -> None:
        super().__init__(entity)

    def create(self, new_record: EntityType | BaseModel, db: SyncSessionType = None) -> EntityType:
        """Creates a new record in the database.

        Args:
            new_record (EntityType | BaseModel): The new record to be created. It can be an
                instance of EntityType or BaseModel.
            db (SyncSessionType, optional): The database session. Defaults to None.

        Returns:
            EntityType: The created record.

        """
        return (self.create_all([new_record], db))[0]

    def create_all(
        self, new_records: list[EntityType | BaseModel], db: SyncSessionType = None
    ) -> list[EntityType]:
        """Creates multiple new records in the database.

        Args:
            new_records (List[EntityType | BaseModel]): A list of new records to be created.
                Each record can be an instance of EntityType or BaseModel.
            db (SyncSessionType, optional): The database session. Defaults to None.

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
        db.flush()
        return items

    @staticmethod
    def save(db: SyncSessionType = None) -> None:
        """Saves the current transaction to the database.

        Args:
            db (SyncSessionType, optional): The database session. Defaults to None.

        Returns:
            None.
        """
        db.flush() if db.in_nested_transaction() else db.commit()

    def find_one(
        self, search_filter: str | FindOneOptions, db: SyncSessionType = None
    ) -> EntityType | None:
        """Finds a single record that matches the given search filter.

        Args:
            search_filter (str | FindOneOptions): The filter criteria to search for the record.
            db (SyncSessionType, optional): The database session. Defaults to None.

        Returns:
            EntityType | None: The found record or None if no record matches the search filter.

        """
        select_statement = self.statement_constructor.build_select_statement(search_filter).limit(1)
        result = db.execute(select_statement).scalars().first()

        return result if result else None

    def find_one_or_fail(
        self, search_filter: str | FindOneOptions, db: SyncSessionType = None
    ) -> EntityType:
        """Finds a single record that matches the given search filter or raises an exception if
            no record is found.

        Args:
            search_filter (str | FindOneOptions): The filter criteria to search for the record.
            db (SyncSessionType, optional): The database session. Defaults to None.

        Returns:
            EntityType: The found record.

        Raises:
            NotFoundException: If no record matches the search filter.

        """
        select_statement = self.statement_constructor.build_select_statement(search_filter).limit(2)
        try:
            return db.execute(select_statement).scalar_one()

        except NoResultFound:
            entity_name = self.entity.__name__
            message = (
                f'Could not find any entity of type "{entity_name}" that matches with the '
                f"search filter"
            )
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
    def find(
        self, stmt_or_filter: FindManyOptions | Select = None, db: SyncSessionType = None
    ) -> Sequence[EntityType]:
        """Finds multiple records that match the given filter criteria or SQL statement.

        Args:
            stmt_or_filter (FindManyOptions | Select, optional): The filter criteria or SQL
                statement to search for the records. Defaults to None.
            db (SyncSessionType, optional): The database session. Defaults to None.

        Returns:
            Sequence[EntityType]: A sequence of found records.

        """
        message = f"Unsupported type: {type(stmt_or_filter)}"
        self.logger.debug(message)
        raise NotImplementedError(message)

    @find.register
    def _(
        self, options: FindManyOptions | dict | None, db: SyncSessionType = None
    ) -> Sequence[EntityType]:
        """Implementation when stmt_or_filter is an instance of FindManyOptions."""
        select_statement = self.statement_constructor.build_select_statement(options)
        return self.find(select_statement, db=db)  # Call the method registered for Select

    @find.register
    def _(self, select_stmt: Select, db: SyncSessionType = None) -> Sequence[EntityType]:
        """Implementation when stmt_or_filter is an instance of Select."""
        return db.execute(select_stmt).scalars().all()

    @singledispatchmethod
    def count(
        self, stmt_or_filter: FindManyOptions | Select = None, db: SyncSessionType = None
    ) -> int:
        """Counts the number of records that match the given filter criteria or SQL statement.

        Args:
            stmt_or_filter (FindManyOptions | Select, optional): The filter criteria or SQL
                statement to count the records. Defaults to None.
            db (SyncSessionType, optional): The database session. Defaults to None.

        Returns:
            int: The count of records that match the filter criteria or SQL statement.

        """
        message = f"Unsupported type: {type(stmt_or_filter)}"
        self.logger.debug(message)
        raise NotImplementedError(message)

    @count.register
    def _(self, options: FindManyOptions | dict | None, db: SyncSessionType = None) -> int:
        """Implementation when stmt_or_filter is an instance of FindManyOptions."""
        select_statement = self.statement_constructor.build_select_statement(options)
        return self.count(select_statement, db=db)

    @count.register
    def _(self, select_stmt: Select, db: SyncSessionType = None) -> int:
        """Implementation when stmt_or_filter is an instance of Select."""
        stmt = select(func.count()).select_from(
            select_stmt.limit(None)
            .offset(None)
            .order_by(None)
            .with_only_columns(literal_column("1"), maintain_column_froms=True)
            .subquery()
        )
        return db.scalar(stmt)

    @singledispatchmethod
    def find_and_count(
        self, search_filter: FindManyOptions | Pagination = None, db: SyncSessionType = None
    ) -> tuple[Sequence[EntityType], int]:
        """Finds multiple records that match the given filter criteria and counts the total number
            of matching records.

        Args:
            search_filter (FindManyOptions, optional): The filter criteria to search for the
                records. Defaults to None.
            db (SyncSessionType, optional): The database session. Defaults to None.

        Returns:
            Tuple[Sequence[EntityType], int]: A tuple containing a sequence of found records and
                the count of matching records.

        """
        message = f"Unsupported type: {type(search_filter)}"
        self.logger.debug(message)
        raise NotImplementedError(message)

    @find_and_count.register
    def _(
        self, search_filter: Pagination, db: SyncSessionType = None
    ) -> tuple[Sequence[EntityType], int]:
        """Implementation when search_filter is an instance of Pagination."""
        find_many_options = self.statement_constructor.build_options(search_filter)
        return self.find_and_count(find_many_options, db)

    @find_and_count.register
    def _(
        self, search_filter: FindManyOptions | dict | None, db: SyncSessionType = None
    ) -> tuple[Sequence[EntityType], int]:
        """Implementation when search_filter is an instance of FindManyOptions."""
        select_statement = self.statement_constructor.build_select_statement(search_filter)
        count = self.count(select_statement, db)
        result = self.find(select_statement, db)

        return result, count

    def update(
        self,
        update_filter: str | UpdateOptions,
        model_data: BaseModel | dict,
        db: SyncSessionType = None,
    ) -> UpdateResult:
        """Updates a record in the database that matches the given search filter with the provided model data.

        Args:
            update_filter (str | UpdateOptions): The search filter to apply. It can be a string or an instance of
                UpdateOptions.
            model_data (BaseModel | dict): The data to update the record with. It can be an instance of BaseModel or
                a dictionary.
            db (SyncSessionType, optional): The database session. Defaults to None.

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
        res = db.execute(stmt, params)

        self.save(db)

        objs = res.scalars().all()
        affected = len(objs)
        return UpdateResult(raw=objs, affected=affected, generated_maps=[])

    def delete(
        self, delete_statement: str | FindOneOptions | ReturningDelete, db: SyncSessionType = None
    ) -> DeleteResult:
        """Deletes a record that matches the given delete statement or filter criteria.

        Args:
            delete_statement (str | FindOneOptions | ReturningDelete): The delete statement or
                filter criteria to find the record to be deleted.
            db (SyncSessionType, optional): The database session. Defaults to None.

        Returns:
            DeleteResult: The result of the delete operation, including the raw data of deleted
                records and the number of affected records.

        """
        if isinstance(delete_statement, Delete):
            res = db.execute(delete_statement)
            objs = res.all()
        else:
            stmt = self.statement_constructor.build_delete_statement(delete_statement).returning(
                self.entity
            )
            res = db.execute(stmt)
            objs = res.scalars().all()

        self.save(db)

        affected = len(objs)
        return DeleteResult(raw=objs, affected=affected)

    def soft_delete(
        self, update_filter: str | UpdateOptions, db: SyncSessionType = None
    ) -> UpdateResult:
        try:
            with db.begin_nested():
                response = self.repo_utils.soft_delete_cascade_from_parent(
                    self.entity,
                    update_filter=update_filter,
                    db=db,
                )

            self.save(db)
            return response

        except Exception as e:
            raise e
