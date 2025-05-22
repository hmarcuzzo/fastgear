import pytest
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase

from fastgear.types.generic_types_var import ColumnsQueryType, EntityType


class TestBase(DeclarativeBase):
    pass


class TestEntity(TestBase):
    __tablename__ = "test_entity"

    id = Column(Integer, primary_key=True)
    name = Column(String)


class TestModel(BaseModel):
    id: int
    name: str


@pytest.mark.describe("🧪  GenericTypesVar")
class TestGenericTypesVar:
    @pytest.mark.it("✅  Should accept SQLAlchemy Base model as EntityType")
    def test_entity_type_with_base_model(self) -> None:
        def test_function(entity: EntityType) -> EntityType:
            return entity

        result = test_function(TestEntity())
        assert isinstance(result, TestEntity)

    @pytest.mark.it("✅  Should accept SQLAlchemy Base model class as EntityType")
    def test_entity_type_with_base_model_class(self) -> None:
        def test_function(entity_class: type[EntityType]) -> type[EntityType]:
            return entity_class

        result = test_function(TestEntity)
        assert result == TestEntity

    @pytest.mark.it("✅  Should accept Pydantic BaseModel as ColumnsQueryType")
    def test_columns_query_type_with_base_model(self) -> None:
        def test_function(model: ColumnsQueryType) -> ColumnsQueryType:
            return model

        result = test_function(TestModel)
        assert result == TestModel

    @pytest.mark.it("✅  Should accept Pydantic BaseModel instance as ColumnsQueryType")
    def test_columns_query_type_with_base_model_instance(self) -> None:
        def test_function(model: ColumnsQueryType) -> ColumnsQueryType:
            return model

        result = test_function(TestModel(id=1, name="test"))
        assert isinstance(result, TestModel)
        assert result.id == 1
        assert result.name == "test"

    @pytest.mark.it("✅  Should work with multiple type variables in same function")
    def test_multiple_type_variables(self) -> None:
        def test_function(
            entity: EntityType, model: ColumnsQueryType
        ) -> tuple[EntityType, ColumnsQueryType]:
            return entity, model

        entity = TestEntity()
        model = TestModel(id=1, name="test")
        result_entity, result_model = test_function(entity, model)

        assert isinstance(result_entity, TestEntity)
        assert isinstance(result_model, TestModel)
        assert result_model.id == 1
        assert result_model.name == "test"
