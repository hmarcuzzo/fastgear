from datetime import datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import InvalidRequestError

from fastgear.common.schema.base_schema import BaseSchema


class _ObjWithAttrs:
    def __init__(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


class _ObjWithUnloadedField:
    def __init__(self, _id: UUID, created_at: datetime, *, updated_at_loaded=True) -> None:
        self.id = _id
        self.created_at = created_at
        self._updated_at_loaded = updated_at_loaded

    @property
    def updated_at(self):
        if not self._updated_at_loaded:
            raise InvalidRequestError("attribute not loaded")
        return datetime.now()


@pytest.mark.describe("🧪  BaseSchema")
class TestBaseSchema:
    @pytest.mark.it("✅  Should validate from dict and parse types")
    def test_model_validate_exclude_unloaded_from_dict(self) -> None:
        uid = uuid4()
        now = datetime.now()
        payload = {"id": str(uid), "created_at": now.isoformat(), "updated_at": now.isoformat()}

        result = BaseSchema.model_validate_exclude_unloaded(payload)

        assert result.id == uid
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.updated_at, datetime)

    @pytest.mark.it("✅  Should validate from object and include loaded attributes")
    def test_model_validate_exclude_unloaded_from_object(self) -> None:
        uid = uuid4()
        now = datetime.now()
        obj = _ObjWithAttrs(id=uid, created_at=now, updated_at=now)

        result = BaseSchema.model_validate_exclude_unloaded(obj)

        assert result.id == uid
        assert result.created_at == now
        assert result.updated_at == now

    @pytest.mark.it(
        "✅  Should skip attributes that raise InvalidRequestError (unloaded) and use defaults"
    )
    def test_skips_unloaded_fields(self) -> None:
        uid = uuid4()
        now = datetime.now()
        obj = _ObjWithUnloadedField(_id=uid, created_at=now, updated_at_loaded=False)

        result = BaseSchema.model_validate_exclude_unloaded(obj)

        assert result.id == uid
        assert result.created_at == now
        # updated_at was unloaded, model should use its default (None)
        assert result.updated_at is None

    @pytest.mark.it(
        "❌  Should raise ValidationError when required fields are missing after excluding unloaded"
    )
    def test_missing_required_field_raises(self) -> None:
        # Create an object that will raise InvalidRequestError for the required 'id'
        class ObjMissingID:
            @property
            def id(self):
                raise InvalidRequestError("id not loaded")

            # created_at exists so that only id is missing
            created_at = datetime.now()
            updated_at = datetime.now()

        with pytest.raises(ValidationError):
            BaseSchema.model_validate_exclude_unloaded(ObjMissingID())
