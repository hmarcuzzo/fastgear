from datetime import datetime
from typing import List

from pydantic.v1 import BaseModel, Field, Extra


class DetailResponseDto(BaseModel):
    loc: List[str] = Field(title="Location")
    msg: str = Field(title="Message")
    type: str = Field(title="Error Type")


class ExceptionResponseDto(BaseModel):
    detail: List[DetailResponseDto]
    status_code: int = Field(422, title="Status Code of the Request")
    timestamp: datetime = Field(title="Timestamp of the Request")
    path: str = Field(title="Request Path")
    method: str = Field(title="Request Method")

    class Config:
        extra = Extra.forbid
