from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.exc import InvalidRequestError

from fastgear.common.schema.custom_base_model_schema import CustomBaseModel


class BaseSchema(CustomBaseModel):
    """Base schema class that includes common fields and a method to validate and exclude unloaded fields.

    Attributes:
        id (UUID): Unique identifier for the schema.
        created_at (datetime | None): Timestamp when the record was created.
        updated_at (datetime | None): Timestamp when the record was last updated.

    """

    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def _extract_fields_to_dict(cls: type[BaseModel], obj: Any) -> dict[str, Any]:
        if isinstance(obj, dict):
            return {key: obj[key] for key in cls.model_fields if key in obj}

        result: dict[str, Any] = {}
        for field_name in cls.model_fields:
            try:
                result[field_name] = getattr(obj, field_name)
            except InvalidRequestError:
                continue
        return result

    @classmethod
    def model_validate_exclude_unloaded(cls: type[BaseModel], obj: Any) -> BaseModel:
        return cls(**cls._extract_fields_to_dict(obj))

    @classmethod
    def to_dict_exclude_unloaded(cls: type[BaseModel], obj: Any) -> dict[str, Any]:
        return cls._extract_fields_to_dict(obj)
