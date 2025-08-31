from datetime import datetime

import pytest
from fastapi import Body, FastAPI, Request
from fastapi.openapi.utils import get_openapi
from httpx import AsyncClient
from pydantic import BaseModel
from pydantic import ValidationError as V2ValidationError
from pydantic.v1 import ValidationError as V1ValidationError
from starlette.exceptions import HTTPException
from starlette.status import (
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from fastgear.common.schema import DetailResponseSchema
from fastgear.handlers.http_exceptions_handler import HttpExceptionsHandler
from fastgear.types.http_exceptions import NotFoundException
from tests.fixtures.api import app

ERROR_TYPES = tuple(t for t in (V2ValidationError, V1ValidationError) if t is not None)


@pytest.mark.describe("🧪 HttpExceptionsHandler")
class TestHttpExceptionsHandler:
    @staticmethod
    def setup_method():
        HttpExceptionsHandler(app)

    @pytest.mark.anyio
    @pytest.mark.it("✅ Should handle Starlette HTTP exceptions correctly")
    async def test_starlette_http_exception_handling(self, async_client: AsyncClient):
        @app.get("/test")
        async def test_endpoint():
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Not Found")

        response = await async_client.get("/test")

        assert response.status_code == HTTP_404_NOT_FOUND
        assert response.json() == {
            "detail": [{"loc": [], "msg": "Not Found", "type": "Starlette HTTP Exception"}],
            "status_code": HTTP_404_NOT_FOUND,
            "timestamp": response.json()["timestamp"],
            "path": "/test",
            "method": "GET",
        }

    @pytest.mark.anyio
    @pytest.mark.it("✅ Should handle FastAPI validation exceptions correctly")
    async def test_fastapi_validation_exception_handling(self, async_client: AsyncClient):
        class ItemIn(BaseModel):
            qty: int

        @app.post("/items")
        async def create_item(payload: ItemIn = Body(...)):
            return {"ok": True}

        resp = await async_client.post("/items", json={"qty": "not-an-int"})
        assert resp.status_code == HTTP_422_UNPROCESSABLE_ENTITY

        # top-level envelope produced by global_exception_error_message(...)
        data = resp.json()
        assert data["status_code"] == HTTP_422_UNPROCESSABLE_ENTITY
        assert data["path"] == "/items"
        assert data["method"] == "POST"
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)

        # details list comes from exc.errors() mapped into DetailResponseSchema
        assert isinstance(data["detail"], list)
        assert len(data["detail"]) > 0

        # DetailResponseSchema fields you populate: loc, msg, type
        first = data["detail"][0]
        assert "loc" in first
        assert isinstance(first["loc"], list)
        assert "msg" in first
        assert isinstance(first["msg"], str)
        assert "type" in first
        assert isinstance(first["type"], str)

    @pytest.mark.anyio
    @pytest.mark.it("✅ Should handle custom HTTP exceptions correctly")
    async def test_custom_http_exception_handling(self, async_client: AsyncClient):
        @app.get("/boom")
        async def boom():
            raise NotFoundException(loc=["path", "resource"], msg="Resource not found")

        resp = await async_client.get("/boom")

        # --- Assertions ---
        assert resp.status_code == HTTP_404_NOT_FOUND

        body = resp.json()
        assert body["status_code"] == HTTP_404_NOT_FOUND
        assert body["path"] == "/boom"
        assert body["method"] == "GET"
        assert "timestamp" in body

        # Detail payload assertions
        assert isinstance(body["detail"], list)
        assert len(body["detail"]) >= 1

        detail = body["detail"][0]
        assert "loc" in detail
        assert isinstance(detail["loc"], list)
        assert "msg" in detail
        assert "type" in detail

        # Specific values set in the NotFoundException
        assert "resource" in detail["loc"]
        assert detail["msg"] == "Resource not found"
        assert detail["type"] == "Not Found"

    @pytest.mark.it("✅ Should generate global exception error messages correctly")
    def test_global_exception_error_message_generation(self):
        request = self._create_request("/test")

        detail = DetailResponseSchema(
            loc=["body", "qty"], msg="value is not a valid integer", type="type_error.integer"
        )

        result = HttpExceptionsHandler.global_exception_error_message(
            status_code=422, detail=detail, request=request
        )

        # Assert top-level fields
        assert result.status_code == HTTP_422_UNPROCESSABLE_ENTITY
        assert result.path == "/test"
        assert result.method == "GET"
        assert isinstance(result.timestamp, datetime)

        # Assert detail normalization and structure
        assert isinstance(result.detail, list)
        assert len(result.detail) == 1

        d0 = result.detail[0]
        assert d0.loc == ["body", "qty"]
        assert d0.msg == "value is not a valid integer"
        assert d0.type in {"type_error.integer", "type_error"}

        # Assert dict conversion
        as_dict = result.dict()
        assert as_dict["status_code"] == HTTP_422_UNPROCESSABLE_ENTITY
        assert as_dict["path"] == "/test"
        assert as_dict["method"] == "GET"
        assert isinstance(as_dict["detail"], list)
        assert len(as_dict["detail"]) == 1
        assert as_dict["detail"][0]["loc"] == ["body", "qty"]

    # @pytest.mark.it("✅ Should customize error response schema in OpenAPI documentation correctly")
    # def test_custom_error_response_schema(self):
    #     # TODO: Implement test logic for customizing error response schema in OpenAPI documentation
    #     pass

    @pytest.mark.anyio
    @pytest.mark.it("❌ Should fail to handle unsupported HTTP exceptions")
    async def test_unsupported_http_exception_handling(self, async_client: AsyncClient):
        @app.get("/unsupported")
        async def unsupported():
            # Not covered by handlers
            raise RuntimeError("boom")

        resp = await async_client.get("/unsupported")

        # Falls back to FastAPI/Starlette default 500 handler
        assert resp.status_code == HTTP_500_INTERNAL_SERVER_ERROR
        assert resp.headers.get("content-type", "").startswith("application/json") is False

    @pytest.mark.it("❌ Should fail to generate error messages for invalid inputs")
    @pytest.mark.parametrize(
        "bad_detail",
        [None, "oops", 123, {"unexpected": "fields"}, [{"loc": None, "msg": 123, "type": None}]],
        ids=["none", "str", "int", "dict-missing-fields", "list-wrong-types"],
    )
    def test_invalid_error_message_generation(self, bad_detail: object):
        request = self._create_request("/invalid")

        with pytest.raises(ERROR_TYPES) as exc:
            HttpExceptionsHandler.global_exception_error_message(
                status_code=422, detail=bad_detail, request=request
            )

        errors = exc.value.errors()
        assert errors, "Expected at least one pydantic error"

        assert any(e.get("loc", [])[0] == "detail" for e in errors)

    @pytest.mark.anyio
    @pytest.mark.it("❌ Should fail to customize error response schema with invalid data")
    async def test_invalid_error_response_schema(
        self, monkeypatch: pytest.MonkeyPatch, async_client: AsyncClient
    ):
        def bad_custom_error_response(self, app: FastAPI) -> None:
            def bad_openapi():
                spec = get_openapi(title="Test App", version="1.0.0", routes=app.routes)
                # Inject something JSON-UNserializable into the schema
                spec.setdefault("components", {}).setdefault("schemas", {})[
                    "ExceptionResponseSchema"
                ] = {"example": object()}  # <- not JSON-serializable
                return spec

            # Replace the OpenAPI factory; serialization happens when hitting /openapi.json
            app.openapi = bad_openapi

        monkeypatch.setattr(
            HttpExceptionsHandler, "custom_error_response", bad_custom_error_response, raising=True
        )

        # Construct the handler with the flag so it calls bad_method
        HttpExceptionsHandler(app, add_custom_error_response=True)

        # Request the OpenAPI doc; expect server-side failure due to bad schema
        resp = await async_client.get("/openapi.json")

        assert resp.status_code == HTTP_500_INTERNAL_SERVER_ERROR

        # Body may or may not be JSON depending on FastAPI/Starlette version
        body = None
        try:
            if resp.text and resp.text.strip():
                body = resp.json()
        except ValueError:
            body = None  # not JSON, fine

        # If JSON, confirm it's not your custom envelope and looks like a generic 500
        if isinstance(body, dict):
            assert "status_code" not in body
            assert "path" not in body
            assert "method" not in body
            assert "timestamp" not in body
            assert "detail" in body

    @staticmethod
    def _create_request(path: str, method: str = "GET") -> Request:
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("utf-8"),
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "root_path": "",
        }

        return Request(scope)
