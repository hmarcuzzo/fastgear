from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from fastutils_hmarcuzzo.types.delete_result import DeleteResult
from fastutils_hmarcuzzo.types.find_many_options import FindManyOptions
from fastutils_hmarcuzzo.types.find_one_options import FindOneOptions
from fastutils_hmarcuzzo.types.update_result import UpdateResult

EntityType = TypeVar("EntityType")
SessionType = TypeVar("SessionType")


class AbstractRepository(ABC, Generic[EntityType]):
    def __init__(self, entity: type[EntityType]) -> None:
        self.entity = entity
        self.select_constructor = None
        self.repo_utils = None

    @abstractmethod
    def create(self, new_record: EntityType | Any, db: SessionType = None) -> EntityType:
        """Abstract method to create a new record.

        Args:
            new_record (EntityType | Any): The new record to be created. It can be an instance of EntityType or any other type.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            EntityType: The created record.

        """

    @abstractmethod
    def create_all(
        self, new_records: list[EntityType | Any], db: SessionType = None,
    ) -> list[EntityType]:
        """Abstract method to create multiple records.

        Args:
            new_records (List[EntityType | Any]): A list of new records to be created. Each record can be an instance of
                EntityType or any other type.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            List[EntityType]: A list of the created records.

        """

    @abstractmethod
    def save(
        self, new_record: EntityType | list[EntityType] = None, db: SessionType = None,
    ) -> EntityType | list[EntityType] | None:
        """Abstract method to save records.

        Args:
            new_record (EntityType | List[EntityType], optional): The new record or list of records to be saved.
                Defaults to None.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            EntityType | List[EntityType] | None: The saved record or list of records, or None if no records were saved.

        """

    @staticmethod
    @abstractmethod
    def commit_or_flush(db: SessionType = None) -> None:
        """Abstract method to commit or flush.

        Args:
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            None

        """

    @staticmethod
    @abstractmethod
    def refresh_record(
        new_record: EntityType | list[EntityType], db: SessionType = None,
    ) -> EntityType | list[EntityType]:
        """Abstract method to refresh records.

        Args:
            new_record (EntityType | List[EntityType]): The record or list of records to be refreshed.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            EntityType | List[EntityType]: The refreshed record or list of records.

        """

    @abstractmethod
    def find_one(
        self, search_filter: str | FindOneOptions, db: SessionType = None,
    ) -> EntityType | None:
        """Abstract method to find one record.

        Args:
            search_filter (str | FindOneOptions): The filter criteria to find the record. It can be a string or an
                instance of FindOneOptions.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            EntityType | None: The found record or None if no record matches the filter criteria.

        """

    @abstractmethod
    def find_one_or_fail(
        self, search_filter: str | FindOneOptions, db: SessionType = None,
    ) -> EntityType:
        """Abstract method to find one record or fail if no record is found.

        Args:
            search_filter (str | FindOneOptions): The filter criteria to find the record. It can be a string or an
                instance of FindOneOptions.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            EntityType: The found record.

        Raises:
            NotFoundException: If no record matches the filter criteria.

        """

    @abstractmethod
    def find(
        self, stmt_or_filter: FindManyOptions | Any = None, db: SessionType = None,
    ) -> Sequence[EntityType]:
        """Abstract method to find many records.

        Args:
            stmt_or_filter (FindManyOptions | Any, optional): The filter criteria or statement to find the records.
                Defaults to None.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            Sequence[EntityType]: A sequence of the found records.

        """

    @abstractmethod
    def count(self, stmt_or_filter: FindManyOptions | Any = None, db: SessionType = None) -> int:
        """Abstract method to count without limit and offset the number of rows returned by a Select Statement.
        Implementation can be sync or async.

        Args:
            stmt_or_filter (FindManyOptions | Any, optional): The filter criteria or statement to count the records.
                Defaults to None.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            int: The count of the records.

        """

    @abstractmethod
    def find_and_count(
        self, search_filter: FindManyOptions = None, db: SessionType = None,
    ) -> tuple[Sequence[EntityType], int]:
        """Abstract method to find and count records. Implementation can be sync or async.

        Args:
            search_filter (FindManyOptions, optional): The filter criteria to find the records. Defaults to None.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            Tuple[Sequence[EntityType], int]: A tuple containing a sequence of the found records and the count of the
                records.

        """

    @abstractmethod
    def update(
        self,
        search_filter: str | FindOneOptions,
        model_data: BaseModel | dict,
        db: SessionType = None,
    ) -> UpdateResult:
        """Abstract method to update records. Implementation can be sync or async.

        Args:
            search_filter (str | FindOneOptions): The filter criteria to find the record to be updated. It can be a
                string or an instance of FindOneOptions.
            model_data (BaseModel | dict): The data to update the record with. It can be an instance of BaseModel
                or a dictionary.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            UpdateResult: The result of the update operation.

        """

    @abstractmethod
    def delete(
        self, delete_statement: str | FindOneOptions | Any, db: SessionType = None,
    ) -> DeleteResult:
        """Abstract method to delete records. Implementation can be sync or async.

        Args:
            delete_statement (str | FindOneOptions | Any): The statement or filter criteria to delete the records.
                It can be a string, an instance of FindOneOptions, or any other type.
            db (SessionType, optional): The database session. Defaults to None.

        Returns:
            DeleteResult: The result of the delete operation.

        """
