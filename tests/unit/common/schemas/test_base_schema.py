from datetime import UTC, datetime
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
        return datetime.now(UTC)


@pytest.mark.describe("🧪  BaseSchema")
class TestBaseSchema:
    @pytest.mark.it("✅  Should validate from dict and parse types")
    def test_model_validate_exclude_unloaded_from_dict(self) -> None:
        uid = uuid4()
        now = datetime.now(UTC)
        payload = {"id": str(uid), "created_at": now.isoformat(), "updated_at": now.isoformat()}

        result = BaseSchema.model_validate_exclude_unloaded(payload)

        assert result.id == uid
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.updated_at, datetime)

    @pytest.mark.it("✅  Should validate from object and include loaded attributes")
    def test_model_validate_exclude_unloaded_from_object(self) -> None:
        uid = uuid4()
        now = datetime.now(UTC)
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
        now = datetime.now(UTC)
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
            created_at = datetime.now(UTC)
            updated_at = datetime.now(UTC)

        with pytest.raises(ValidationError):
            BaseSchema.model_validate_exclude_unloaded(ObjMissingID())

    @pytest.mark.it("✅  Should return dict from dict input with only model fields")
    def test_to_dict_from_dict(self) -> None:
        uid = uuid4()
        now = datetime.now(UTC)
        payload = {"id": uid, "created_at": now, "updated_at": now, "extra_field": "ignored"}

        result = BaseSchema.to_dict_exclude_unloaded(payload)

        assert result == {"id": uid, "created_at": now, "updated_at": now}
        assert "extra_field" not in result

    @pytest.mark.it("✅  Should return dict from object with loaded attributes")
    def test_to_dict_from_object(self) -> None:
        uid = uuid4()
        now = datetime.now(UTC)
        obj = _ObjWithAttrs(id=uid, created_at=now, updated_at=now)

        result = BaseSchema.to_dict_exclude_unloaded(obj)

        assert result == {"id": uid, "created_at": now, "updated_at": now}

    @pytest.mark.it("✅  Should skip attributes that raise InvalidRequestError (unloaded)")
    def test_to_dict_skips_unloaded_fields(self) -> None:
        uid = uuid4()
        now = datetime.now(UTC)
        obj = _ObjWithUnloadedField(_id=uid, created_at=now, updated_at_loaded=False)

        result = BaseSchema.to_dict_exclude_unloaded(obj)

        assert result == {"id": uid, "created_at": now}
        assert "updated_at" not in result

    @pytest.mark.it("✅  Should return partial dict when some fields are missing in input dict")
    def test_to_dict_from_partial_dict(self) -> None:
        uid = uuid4()
        payload = {"id": uid}

        result = BaseSchema.to_dict_exclude_unloaded(payload)

        assert result == {"id": uid}
        assert "created_at" not in result
        assert "updated_at" not in result

    @pytest.mark.it("❌  Should return empty dict when all fields raise InvalidRequestError")
    def test_to_dict_all_fields_unloaded(self) -> None:
        class ObjAllUnloaded:
            @property
            def id(self):
                raise InvalidRequestError("id not loaded")

            @property
            def created_at(self):
                raise InvalidRequestError("created_at not loaded")

            @property
            def updated_at(self):
                raise InvalidRequestError("updated_at not loaded")

        result = BaseSchema.to_dict_exclude_unloaded(ObjAllUnloaded())

        assert result == {}

    @pytest.mark.it("❌  Should return empty dict when input dict has no matching fields")
    def test_to_dict_no_matching_fields(self) -> None:
        payload = {"unknown_field": "value", "another_field": 123}

        result = BaseSchema.to_dict_exclude_unloaded(payload)

        assert result == {}

    @pytest.mark.it("❌  Should return empty dict when input dict is empty")
    def test_to_dict_empty_dict(self) -> None:
        result = BaseSchema.to_dict_exclude_unloaded({})

        assert result == {}

    @pytest.mark.it("❌  Should not validate types (raw values preserved)")
    def test_to_dict_does_not_validate_types(self) -> None:
        payload = {"id": "not-a-uuid", "created_at": "invalid-date"}

        result = BaseSchema.to_dict_exclude_unloaded(payload)

        assert result["id"] == "not-a-uuid"
        assert result["created_at"] == "invalid-date"
