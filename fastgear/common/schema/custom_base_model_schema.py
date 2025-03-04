from datetime import datetime

from pydantic import BaseModel


class CustomBaseModel(BaseModel):
    """A custom base model that extends Pydantic's BaseModel.

    This class provides common configurations and behaviors for other data models in the application.
    """

    class Config:
        """Configuration for the CustomBaseModel.

        Attributes: json_encoders (dict): A dictionary that maps data types to functions that convert them to JSON serializable formats.
        """

        json_encoders = {datetime: lambda v: v.isoformat()}
