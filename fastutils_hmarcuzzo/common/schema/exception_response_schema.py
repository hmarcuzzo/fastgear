from datetime import datetime

from pydantic.v1 import BaseModel, Extra, Field


class DetailResponseSchema(BaseModel):
    loc: list[str] = Field(title="Location")
    msg: str = Field(title="Message")
    type: str = Field(title="Error Type")


class ExceptionResponseSchema(BaseModel):
    detail: list[DetailResponseSchema]
    status_code: int = Field(422, title="Status Code of the Request")
    timestamp: datetime = Field(title="Timestamp of the Request")
    path: str = Field(title="Request Path")
    method: str = Field(title="Request Method")

    class Config:
        extra = Extra.forbid
