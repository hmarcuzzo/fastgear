from typing import Any, ClassVar

import pytest
from fastapi import APIRouter, Depends, Request
from starlette.status import HTTP_200_OK
from starlette.testclient import TestClient

from fastgear.decorators import controller


@pytest.mark.describe("🧪  ControllerDecorator")
class TestControllerDecorator:
    @pytest.fixture(autouse=True)
    def router(self) -> APIRouter:
        return APIRouter()

    @pytest.mark.it("✅  Should register routes correctly")
    def test_response_models(self, router: APIRouter) -> None:
        expected_response = "home"

        @controller(router)
        class Controller:
            def __init__(self) -> None:
                self.one = 1
                self.two = 2

            @router.get("/")
            def string_response(self) -> str:
                return expected_response

            @router.get("/sum")
            def int_response(self) -> int:
                return self.one + self.two

        client = TestClient(router)
        response_1 = client.get("/")
        assert response_1.status_code == HTTP_200_OK
        assert response_1.json() == expected_response

        response_2 = client.get("/sum")
        assert response_2.status_code == HTTP_200_OK
        assert response_2.content == b"3"

    @pytest.mark.it("✅  Should handle dependencies correctly")
    def test_dependencies(self, router: APIRouter) -> None:
        def dependency_one() -> int:
            return 1

        def dependency_two() -> int:
            return 2

        @controller(router)
        class Controller:
            one: int = Depends(dependency_one)

            def __init__(self, two: int = Depends(dependency_two)):
                self.two = two

            @router.get("/")
            def int_dependencies(self) -> int:
                return self.one + self.two

        client = TestClient(router)
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.content == b"3"

    @pytest.mark.it("✅  Should ignore ClassVar attributes")
    def test_class_var(self, router: APIRouter) -> None:
        @controller(router)
        class Controller:
            class_var: ClassVar[int]

            @router.get("/")
            def g(self) -> bool:
                return hasattr(self, "class_var")

        client = TestClient(router)
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.content == b"false"

    @pytest.mark.it("✅  Should preserve the order of route registration")
    def test_routes_path_order_preserved(self, router: APIRouter) -> None:
        @controller(router)
        class Controller:
            @router.get("/test")
            def get_test(self) -> int:
                return 1

            @router.get("/{any_path}")
            def get_any_path(self, any_path) -> int:  # Alphabetically before `get_test`
                return 2

        client = TestClient(router)
        assert client.get("/test").json() == 1
        assert client.get("/any_other_path").json() == 2  # noqa: PLR2004

    @pytest.mark.it("✅  Should handle multiple paths for a single method")
    def test_multiple_paths(self, router: APIRouter) -> None:
        @controller(router)
        class Controller:
            @router.get("/items")
            @router.get("/items/{custom_path:path}")
            @router.get("/database/{custom_path:path}")
            def root(self, custom_path: str | None = None) -> Any:
                return {"custom_path": custom_path} if custom_path else []

        client = TestClient(router)
        assert client.get("/items").json() == []
        assert client.get("/items/1").json() == {"custom_path": "1"}
        assert client.get("/database/abc").json() == {"custom_path": "abc"}

    @pytest.mark.it("✅  Should handle query parameters correctly")
    def test_query_parameters(self, router: APIRouter) -> None:
        @controller(router)
        class Controller:
            @router.get("/route")
            def root(self, param: int | None = None) -> int:
                return param if param else 0

        client = TestClient(router)
        assert client.get("/route").json() == 0
        assert client.get("/route?param=3").json() == 3  # noqa: PLR2004

    @pytest.mark.it("✅  Should apply prefix correctly")
    def test_prefix(self) -> None:
        router = APIRouter(prefix="/api")

        @controller(router)
        class Controller:
            @router.get("/item")
            def root(self) -> str:
                return "hello"

        client = TestClient(router)
        response = client.get("/api/item")
        assert response.status_code == HTTP_200_OK
        assert response.json() == "hello"

    @pytest.mark.it("✅  Should resolve url_for correctly between controllers")
    def test_url_for(self, router: APIRouter) -> None:
        @controller(router)
        class Foo:
            @router.get("/foo")
            def example(self, request: Request) -> str:
                return str(request.url_for("Bar.example"))

        @controller(router)
        class Bar:
            @router.get("/bar")
            def example(self, request: Request) -> str:
                return str(request.url_for("Foo.example"))

        client = TestClient(router)
        response = client.get("/foo")
        assert response.json() == "http://testserver/bar"

    @pytest.mark.it("✅  Should not duplicate tags from router and route")
    def test_duplicate_tag_removal(self) -> None:
        router = APIRouter(prefix="/api", tags=["test"])

        @controller(router)
        class Controller:
            @router.get("/item")
            def root(self) -> str:
                return "hello"

        assert router.routes[0].tags == ["test"]
