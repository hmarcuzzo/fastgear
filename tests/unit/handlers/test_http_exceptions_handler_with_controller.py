import pytest
from fastapi import APIRouter, FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel
from starlette.status import HTTP_200_OK

from fastgear.decorators.controller_decorator import controller
from fastgear.handlers.http_exceptions_handler import HttpExceptionsHandler


class DummyModel(BaseModel):
    name: str
    qty: int


@pytest.mark.describe("🧪  HttpExceptionsHandler with @controller decorator")
class TestHttpExceptionsHandlerWithController:
    @pytest.mark.anyio
    @pytest.mark.it("✅  Should customize error response schema for controller endpoints")
    async def test_custom_error_response_with_controller(self):
        app = FastAPI()
        router = APIRouter()

        @controller(router)
        class ItemController:
            @router.post("/items")
            def post(self, payload: DummyModel) -> dict:
                return {"ok": True, "data": payload.model_dump()}

        app.include_router(router)
        HttpExceptionsHandler(app, add_custom_error_response=True)

        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/openapi.json")

            assert resp.status_code == HTTP_200_OK
            spec = resp.json()

            assert "/items" in spec.get("paths", {}), "/items path not found in OpenAPI schema"
            assert "post" in spec["paths"]["/items"], "POST method not found for /items"

            responses = spec["paths"]["/items"]["post"].get("responses", {})
            assert "422" in responses, "422 response not found"

            response_422 = responses["422"]
            schema_ref = (
                response_422.get("content", {}).get("application/json", {}).get("schema", {})
            )

            assert "$ref" in schema_ref, "No $ref found in 422 response schema"
            assert "ExceptionResponseSchema" in schema_ref["$ref"], (
                f"Expected ExceptionResponseSchema reference, got: {schema_ref['$ref']}"
            )

            schemas = spec.get("components", {}).get("schemas", {})
            assert "ExceptionResponseSchema" in schemas, "ExceptionResponseSchema not in schemas"
            assert "HTTPValidationError" not in schemas, "HTTPValidationError should be removed"
            assert "ValidationError" not in schemas, "ValidationError should be removed"
