import json
from copy import deepcopy
from datetime import datetime
from typing import List

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from fastutils_hmarcuzzo.common.dto.exception_response_dto import (
    DetailResponseDto,
    ExceptionResponseDto,
)
from fastutils_hmarcuzzo.types.exceptions import (
    BadRequestException,
    NotFoundException,
    UnauthorizedException,
    ForbiddenException,
)
from fastutils_hmarcuzzo.utils.json_utils import JsonUtils


class HttpExceptionsHandler:
    def __init__(self, app: FastAPI):
        self.app = app
        self.add_exceptions_handler()
        self.custom_error_response(app)

    def add_exceptions_handler(self):
        @self.app.exception_handler(StarletteHTTPException)
        async def http_exception_handler(request: Request, exc) -> Response:
            return Response(
                status_code=exc.status_code,
                content=json.dumps(
                    self.global_exception_error_message(
                        status_code=exc.status_code,
                        detail=DetailResponseDto(
                            loc=[], msg=exc.detail, type="starlette_http_exception"
                        ),
                        request=request,
                    ).__dict__,
                    default=JsonUtils.json_serial,
                ),
            )

        @self.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(
            request: Request, exc: RequestValidationError
        ) -> Response:
            return Response(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                content=json.dumps(
                    self.global_exception_error_message(
                        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=[DetailResponseDto(**detail) for detail in exc.errors()],
                        request=request,
                    ).__dict__,
                    default=JsonUtils.json_serial,
                ),
            )

        @self.app.exception_handler(BadRequestException)
        @self.app.exception_handler(UnauthorizedException)
        @self.app.exception_handler(ForbiddenException)
        @self.app.exception_handler(NotFoundException)
        async def custom_exceptions_handler(request: Request, exc: BadRequestException) -> Response:
            detail_dict = deepcopy(exc.__dict__)
            detail_dict.pop("status_code", None)

            return Response(
                status_code=exc.status_code,
                content=json.dumps(
                    self.global_exception_error_message(
                        status_code=exc.status_code,
                        detail=DetailResponseDto(**detail_dict),
                        request=request,
                    ).__dict__,
                    default=JsonUtils.json_serial,
                ),
            )

    @staticmethod
    def global_exception_error_message(
        status_code: int,
        detail: DetailResponseDto | List[DetailResponseDto],
        request: Request,
    ) -> ExceptionResponseDto:
        if not isinstance(detail, List):
            detail = [detail]

        return ExceptionResponseDto(
            detail=detail,
            status_code=status_code,
            timestamp=datetime.now().astimezone(),
            path=request.url.path,
            method=request.method,
        )

    @staticmethod
    def custom_error_response(app: FastAPI):
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # not quite the ideal scenario but this is the best we can do to override the default
        # error schema. See
        from fastapi.openapi.constants import REF_PREFIX
        from pydantic.v1.schema import schema

        paths = openapi_schema["paths"]
        for path in paths:
            for method in paths[path]:
                if paths[path][method]["responses"].get("422"):
                    paths[path][method]["responses"]["422"] = {
                        "description": "Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"{REF_PREFIX}ExceptionResponseDto"}
                            }
                        },
                    }

        error_response_defs = schema(
            [ExceptionResponseDto],
            ref_prefix=REF_PREFIX,
            ref_template=f"{REF_PREFIX}{{model}}",
        )
        openapi_schemas = openapi_schema["components"]["schemas"]
        openapi_schemas.update(error_response_defs["definitions"])
        openapi_schemas.pop("ValidationError")
        openapi_schemas.pop("HTTPValidationError")

        app.openapi_schema = openapi_schema
