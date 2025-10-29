import pytest

from fastgear.common.database.abstract_repository import AbstractRepository
from fastgear.common.database.sqlalchemy.repository_utils.base_repository_utils import (
    BaseRepositoryUtils,
)


class DummyEntity:
    pass


class DummyRepo(AbstractRepository[DummyEntity]):
    # Minimal concrete implementations of abstract methods for testing init/utility behavior
    def create(self, new_record: DummyEntity | object, db=None) -> DummyEntity:
        return new_record

    def create_all(self, new_records: list[DummyEntity | object], db=None) -> list[DummyEntity]:
        return list(new_records)

    @staticmethod
    def save(new_record: DummyEntity | list[DummyEntity] = None, db=None):
        return new_record

    @staticmethod
    def commit_or_flush(db=None) -> None:
        return None

    @staticmethod
    def refresh_record(new_record: DummyEntity | list[DummyEntity], db=None):
        return new_record

    def find_one(self, search_filter, db=None):
        return None

    def find_one_or_fail(self, search_filter, db=None):
        raise LookupError("not found")

    def find(self, stmt_or_filter=None, db=None):
        return []

    def count(self, stmt_or_filter=None, db=None) -> int:
        return 0

    def find_and_count(self, search_filter=None, db=None):
        return ([], 0)

    def update(self, search_filter, model_data, db=None):
        return {"raw": None, "affected": 0, "generated_maps": None}

    def delete(self, delete_statement, db=None):
        return {"raw": None, "affected": 0}

    def soft_delete(self, search_filter, db=None):
        return {"raw": None, "affected": 0}


@pytest.mark.describe("🧪  AbstractRepository")
class TestAbstractRepository:
    @pytest.mark.it("✅  Should not allow instantiation of the abstract class")
    def test_abstract_class_cannot_be_instantiated(self):
        # AbstractRepository has abstract methods and should not be instantiable
        with pytest.raises(TypeError):
            AbstractRepository(DummyEntity)

    @pytest.mark.it("✅  Should allow instantiation of a concrete subclass and test methods")
    def test_concrete_subclass_initialization_and_methods(self):
        repo = DummyRepo(DummyEntity)

        # basic attributes set in AbstractRepository.__init__
        assert repo.entity is DummyEntity
        assert hasattr(repo, "statement_constructor")
        assert repo.statement_constructor.entity is DummyEntity
        assert isinstance(repo.repo_utils, BaseRepositoryUtils)
        assert repo.logger is not None

        # static methods are callable on class and instance
        assert DummyRepo.save("x") == "x"
        assert repo.save("y") == "y"
        assert DummyRepo.commit_or_flush() is None

        # refresh_record should return what was passed through
        assert DummyRepo.refresh_record([1, 2, 3]) == [1, 2, 3]

        # create_all should return a list
        assert repo.create_all([DummyEntity(), DummyEntity()])
        assert isinstance(repo.create_all([], None), list)
