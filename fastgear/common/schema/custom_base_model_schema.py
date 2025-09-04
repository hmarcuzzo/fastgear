from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CustomBaseModel(BaseModel):
    """A custom base model that extends Pydantic's BaseModel.

    This class provides common configurations and behaviors for other data models in the application.
    """

    # model_config (ConfigDict): Pydantic v2 configuration that registers JSON encoders.
    # Maps datetime objects to ISO 8601 strings using datetime.isoformat() so datetime fields
    # are JSON-serializable (e.g. when calling .model_dump_json() or similar serializers).
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
