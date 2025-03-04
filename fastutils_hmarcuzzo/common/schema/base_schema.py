from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.exc import InvalidRequestError

from fastutils_hmarcuzzo.common.schema.custom_base_model_schema import CustomBaseModel


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
    def model_validate_exclude_unloaded(cls: type[BaseModel], obj: Any) -> BaseModel:
        """Validates the model and excludes fields that are not loaded.

        This method attempts to get the attribute for each field in the model. If an InvalidRequestError
        is raised, it means the field is not loaded, and it is excluded from the validation.

        Args:
            cls (Type[BaseModel]): The class type of the model.
            obj (Any): The object to validate, can be a dictionary or an instance of the model.

        Returns:
            BaseModel: An instance of the model with only the loaded fields.

        """
        obj_dict = {}
        if isinstance(obj, dict):
            obj_dict = obj
        else:
            for field_name in cls.__fields__:
                try:
                    # Attempt to get the attribute, if it raises an InvalidRequestError, it is not loaded
                    value = getattr(obj, field_name)
                    obj_dict[field_name] = value
                except InvalidRequestError:
                    # Don't add the field if it is not loaded
                    continue

        return cls(**obj_dict)
