from typing import Generic, TypeVar, List, Tuple

from pydantic import BaseModel
from sqlalchemy.orm import Session

from fastutils_hmarcuzzo.common.database.sqlalchemy.repository_utils.query_constructor import (
    QueryConstructor,
)
from fastutils_hmarcuzzo.types.delete_result import DeleteResult
from fastutils_hmarcuzzo.types.exceptions import NotFoundException
from fastutils_hmarcuzzo.types.find_many_options import FindManyOptions
from fastutils_hmarcuzzo.types.find_one_options import FindOneOptions
from fastutils_hmarcuzzo.types.update_result import UpdateResult

T = TypeVar("T")


class BaseRepository(Generic[T]):
    entity: T = None

    def __init__(self, entity: T):
        self.entity = entity
        self.query_constructor = QueryConstructor(entity)

    async def create(self, db: Session, new_record: T | BaseModel) -> T:
        if isinstance(new_record, BaseModel):
            model_data = new_record.model_dump(exclude_unset=True)
            new_record = self.entity(**model_data)

        db.add(new_record)
        db.flush()
        return new_record

    @staticmethod
    def save(db: Session, new_record: T | List[T] = None) -> T:
        db.commit()

        if new_record:
            BaseRepository.refresh_record(db, new_record)
        return new_record

    @staticmethod
    def refresh_record(
        db: Session,
        new_record: T | List[T],
    ) -> T | List[T]:
        db.refresh(new_record) if not isinstance(new_record, List) else (
            db.refresh(_en) for _en in new_record
        )
        return new_record

    async def find_one(self, db: Session, search_filter: str | FindOneOptions) -> T:
        query = self.query_constructor.build_query(db, search_filter)
        result = query.first()

        return result

    async def find_one_or_fail(
        self,
        db: Session,
        search_filter: str | FindOneOptions,
    ) -> T:
        result = await self.find_one(db, search_filter)

        if not result:
            entity_name = self.entity.__name__
            message = f'Could not find any entity of type "{entity_name}" that matches with the search filter'
            raise NotFoundException(message, [entity_name])

        return result

    async def find(self, db: Session, search_filter: FindManyOptions = None) -> List[T]:
        query = self.query_constructor.build_query(db, search_filter)
        result = query.all()

        return result

    async def find_and_count(
        self, db: Session, search_filter: FindManyOptions = None
    ) -> Tuple[List[T], int]:
        query = self.query_constructor.build_query(db, search_filter)
        count = query.offset(None).limit(None).count()
        result = query.all()

        return result, count

    async def update(
        self,
        db: Session,
        search_filter: str | FindOneOptions,
        model_data: BaseModel | dict,
    ) -> UpdateResult:
        record = await self.find_one_or_fail(db, search_filter)

        if isinstance(model_data, BaseModel):
            model_data = model_data.model_dump(exclude_unset=True)

        for key, value in model_data.items():
            setattr(record, key, value)

        db.flush() if db.transaction.nested else db.commit()
        return UpdateResult(raw=[], affected=1, generatedMaps=[])

    async def delete(self, db: Session, search_filter: str | FindOneOptions) -> DeleteResult:
        record = await self.find_one_or_fail(db, search_filter)

        db.delete(record)
        db.flush() if db.transaction.nested else db.commit()

        return DeleteResult(raw=[], affected=1)
