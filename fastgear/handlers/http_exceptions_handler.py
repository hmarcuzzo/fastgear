import json
from copy import deepcopy
from datetime import UTC, datetime

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_CONTENT

from fastgear.common.schema import DetailResponseSchema, ExceptionResponseSchema
from fastgear.types.http_exceptions import (
    BadRequestException,
    CustomHTTPExceptionType,
    DuplicateValueException,
    ForbiddenException,
    NotFoundException,
    RateLimitException,
    UnauthorizedException,
    UnprocessableEntityException,
)
from fastgear.utils import JsonUtils


class HttpExceptionsHandler:
    def __init__(self, app: FastAPI, *, add_custom_error_response: bool = False) -> None:
        self.app = app
        self.add_exceptions_handler()
        self.custom_error_response(app) if add_custom_error_response else None

    def add_exceptions_handler(self) -> None:
        """Adds exception handlers to the FastAPI app for handling various HTTP exceptions."""

        @self.app.exception_handler(StarletteHTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException) -> Response:
            """Handles Starlette HTTP exceptions and returns a formatted JSON response.

            Args:
                request (Request): The incoming request object.
                exc (HTTPException): The HTTP exception raised.

            Returns:
                Response: A JSON response with the exception details.

            """
            return Response(
                status_code=exc.status_code,
                headers={"content-type": "application/json"},
                content=json.dumps(
                    self.global_exception_error_message(
                        status_code=exc.status_code,
                        detail=DetailResponseSchema(
                            loc=[], msg=exc.detail, type="Starlette HTTP Exception"
                        ),
                        request=request,
                    ).model_dump(),
                    default=JsonUtils.json_serial,
                ),
            )

        @self.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(
            request: Request, exc: RequestValidationError
        ) -> Response:
            """Handles FastAPI request validation errors and returns a formatted JSON response.

            Args:
                request (Request): The incoming request object.
                exc (RequestValidationError): The validation error exception raised.

            Returns:
                Response: A JSON response with the validation error details.

            """
            return Response(
                status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                headers={"content-type": "application/json"},
                content=json.dumps(
                    self.global_exception_error_message(
                        status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                        detail=[DetailResponseSchema(**detail) for detail in exc.errors()],
                        request=request,
                    ).model_dump(),
                    default=JsonUtils.json_serial,
                ),
            )

        @self.app.exception_handler(BadRequestException)
        @self.app.exception_handler(UnauthorizedException)
        @self.app.exception_handler(ForbiddenException)
        @self.app.exception_handler(NotFoundException)
        @self.app.exception_handler(UnprocessableEntityException)
        @self.app.exception_handler(DuplicateValueException)
        @self.app.exception_handler(RateLimitException)
        async def custom_exceptions_handler(
            request: Request, exc: CustomHTTPExceptionType
        ) -> Response:
            """Handles custom HTTP exceptions and returns a formatted JSON response.

            This function is a FastAPI exception handler that processes various custom HTTP exceptions
            and generates a standardized JSON response containing the exception details.

            Args:
                request (Request): The incoming request object.
                exc (CustomHTTPExceptionType): The custom HTTP exception raised.

            Returns:
                Response: A JSON response with the exception details.

            """
            detail_dict = deepcopy(exc.__dict__)
            detail_dict.pop("status_code", None)

            return Response(
                status_code=exc.status_code,
                headers={"content-type": "application/json"},
                content=json.dumps(
                    self.global_exception_error_message(
                        status_code=exc.status_code,
                        detail=DetailResponseSchema(**detail_dict),
                        request=request,
                    ).model_dump(),
                    default=JsonUtils.json_serial,
                ),
            )

    @staticmethod
    def global_exception_error_message(
        status_code: int,
        detail: DetailResponseSchema | list[DetailResponseSchema],
        request: Request,
    ) -> ExceptionResponseSchema:
        """Generates a standardized error message for exceptions.

        This function creates an `ExceptionResponseSchema` object that includes details about the exception,
        such as the status code, error details, timestamp, request path, and HTTP method.

        Args:
            status_code (int): The HTTP status code of the exception.
            detail (DetailResponseSchema | List[DetailResponseSchema]): The details of the exception. Can be a single
                `DetailResponseSchema` object or a list of such objects.
            request (Request): The incoming request object that triggered the exception.

        Returns:
            ExceptionResponseSchema: An object containing the standardized error message.

        """
        if not isinstance(detail, list):
            detail = [detail]

        return ExceptionResponseSchema(
            detail=detail,
            status_code=status_code,
            timestamp=datetime.now(UTC).astimezone(),
            path=request.url.path,
            method=request.method,
        )

    @staticmethod
    def custom_error_response(app: FastAPI) -> dict:
        """Customizes the error response schema in the FastAPI app's OpenAPI documentation.

        This function modifies the default OpenAPI schema generated by FastAPI to include
        custom error response schemas. It specifically targets the 422 Validation Error response
        and replaces it with a custom schema reference.

        Args:
            app (FastAPI): The FastAPI application instance for which the OpenAPI schema will be customized.

        Returns:
            dict: The customized OpenAPI schema. If the schema has already been generated, it returns the existing
                schema.

        """
        if not app.openapi_schema:
            from fastapi.openapi.constants import REF_PREFIX
            from pydantic.json_schema import models_json_schema

            openapi_schema = app.openapi()

            paths = openapi_schema.get("paths", {})
            for methods in paths.values():
                for details in methods.values():
                    responses = details.get("responses", {})
                    if "422" in responses:
                        responses["422"] = {
                            "description": "Validation Error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": f"{REF_PREFIX}ExceptionResponseSchema"}
                                }
                            },
                        }

            _, defs_schema = models_json_schema(
                [(ExceptionResponseSchema, "validation")], ref_template=f"{REF_PREFIX}{{model}}"
            )
            defs = defs_schema.get("$defs", {})

            openapi_schemas = openapi_schema.setdefault("components", {}).setdefault("schemas", {})
            openapi_schemas.update(defs)
            openapi_schemas.pop("ValidationError", None)
            openapi_schemas.pop("HTTPValidationError", None)

        return app.openapi_schema
