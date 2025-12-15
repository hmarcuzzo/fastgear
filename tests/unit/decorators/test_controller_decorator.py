from typing import Any, ClassVar

import pytest
from fastapi import APIRouter, Depends, FastAPI, Request
from starlette.status import HTTP_200_OK, HTTP_201_CREATED
from starlette.testclient import TestClient

from fastgear.decorators import controller
from fastgear.decorators.controller_decorator import (
    INCLUDE_INIT_PARAMS_KEY,
    RETURN_TYPES_FUNC_KEY,
    _controller,
    _convert_to_title_case,
    _remove_router_tags,
    _update_route_summary,
)


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

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
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

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
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

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
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

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        assert client.get("/test").json() == 1
        assert client.get("/any_other_path").json() == 2

    @pytest.mark.it("✅  Should handle multiple paths for a single method")
    def test_multiple_paths(self, router: APIRouter) -> None:
        @controller(router)
        class Controller:
            @router.get("/items")
            @router.get("/items/{custom_path:path}")
            @router.get("/database/{custom_path:path}")
            def root(self, custom_path: str | None = None) -> Any:
                return {"custom_path": custom_path} if custom_path else []

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
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

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        assert client.get("/route").json() == 0
        assert client.get("/route?param=3").json() == 3

    @pytest.mark.it("✅  Should apply prefix correctly")
    def test_prefix(self) -> None:
        router = APIRouter(prefix="/api")

        @controller(router)
        class Controller:
            @router.get("/item")
            def root(self) -> str:
                return "hello"

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
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

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
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

    @pytest.mark.it("✅  Should include init params when INCLUDE_INIT_PARAMS_KEY is set")
    def test_include_init_params_with_instance(self, router: APIRouter) -> None:
        class Controller:
            def __init__(self, value: int = 5):
                self.value = value

            @router.get("/value")
            def get_value(self) -> int:
                return self.value

        setattr(Controller, INCLUDE_INIT_PARAMS_KEY, True)
        instance = Controller(value=10)
        _controller(router, Controller, instance=instance)

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.get("/value")
        assert response.status_code == HTTP_200_OK
        assert response.json() == 5  # Should use init params, not instance value

    @pytest.mark.it("✅  Should use provided instance when INCLUDE_INIT_PARAMS_KEY is not set")
    def test_use_instance_without_include_init_params(self, router: APIRouter) -> None:
        class Controller:
            def __init__(self, value: int = 5):
                self.value = value

            @router.get("/value")
            def get_value(self) -> int:
                return self.value

        instance = Controller(value=10)
        _controller(router, Controller, instance=instance)

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.get("/value")
        assert response.status_code == HTTP_200_OK
        assert response.json() == 10  # Should use instance value, not default

    @pytest.mark.it("✅  Should register multiple URLs for controller methods")
    def test_multiple_urls_registration(self, router: APIRouter) -> None:
        @controller(router, "/users", "/admin/users")
        class Controller:
            def get(self) -> str:
                return "get_response"

            def post(self) -> str:
                return "post_response"

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Test first URL
        assert client.get("/users").json() == "get_response"
        assert client.post("/users").json() == "post_response"

        # Test second URL
        assert client.get("/admin/users").json() == "get_response"
        assert client.post("/admin/users").json() == "post_response"

    @pytest.mark.it("✅  Should use custom return types when RETURN_TYPES_FUNC_KEY is set")
    def test_custom_return_types_func(self, router: APIRouter) -> None:
        def custom_return_types() -> tuple[
            type[dict[str, Any]], int, dict[str, Any], dict[str, Any]
        ]:
            return (
                dict[str, Any],
                201,
                {
                    "201": {
                        "description": "Custom response",
                        "content": {"application/json": {"example": {"id": 1, "name": "test"}}},
                    }
                },
                {"tags": ["custom"]},
            )

        class Controller:
            def get(self) -> dict[str, Any]:
                return {"id": 1, "name": "item1"}

        setattr(Controller.get, RETURN_TYPES_FUNC_KEY, custom_return_types)
        controller(router, "/items")(Controller)

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.get("/items")
        assert response.status_code == HTTP_201_CREATED
        assert response.json() == {"id": 1, "name": "item1"}

    @pytest.mark.it("✅  Should raise ValueError when route is not APIRoute")
    def test_non_api_route_raises_error(self, router: APIRouter) -> None:
        from starlette.routing import Mount

        @controller(router)
        class Controller:
            def get(self) -> str:
                return "test"

        mount = Mount("/mount", routes=[])
        router.routes.append(mount)

        with pytest.raises(ValueError, match="The provided routes should be of type APIRoute"):

            @controller(router)
            class AnotherController:
                def post(self) -> str:
                    return "test2"

    @pytest.mark.it("✅  Should raise Exception when duplicate route roles exist")
    def test_duplicate_route_roles_raises_error(self, router: APIRouter) -> None:
        @controller(router, "/items")
        class Controller:
            def get(self) -> str:
                return "first"

        with pytest.raises(
            Exception, match="An identical route role has been implemented more then once"
        ):

            @controller(router, "/items")
            class AnotherController:
                def get(self) -> str:
                    return "duplicate"

    @pytest.mark.it("✅  Should not change route name when already prefixed with class name")
    def test_route_name_already_prefixed_not_changed(self, router: APIRouter) -> None:
        @controller(router)
        class Controller:
            @router.get("/prefixed", name="Controller.get")
            def get(self) -> str:
                return "ok"

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.get("/prefixed")
        assert resp.status_code == HTTP_200_OK

        # Find the route and assert the name is unchanged
        matching = [
            r for r in router.routes if hasattr(r, "name") and getattr(r, "path", "") == "/prefixed"
        ]
        assert len(matching) == 1
        assert matching[0].name == "Controller.get"

    @pytest.mark.it("✅  Should skip tag removal when route has no 'tags' attribute")
    def test_remove_router_tags_condition_false(self) -> None:
        router = APIRouter(tags=["api"])  # router has tags

        class DummyRoute:
            def __init__(self) -> None:
                self.path = "/dummy"

        route = DummyRoute()

        # Call helper directly: condition should be False (no 'tags' on route)
        _remove_router_tags(route, router)

        # Route still has no 'tags'; most importantly, no exception was raised
        assert not hasattr(route, "tags")

    @pytest.mark.it("✅  Should use pydantic.v1 import path when PYDANTIC_VERSION major != '2'")
    def test_pydantic_version_not_2_import_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import importlib
        import sys
        import types
        from typing import ClassVar as _ClassVar
        from typing import get_origin as _get_origin

        import pydantic as _pyd

        # Save current module and version
        import fastgear.decorators.controller_decorator as cd

        original_version = getattr(_pyd, "VERSION", "2")

        # Prepare fake pydantic.typing with a compatible is_classvar
        fake_typing = types.ModuleType("pydantic.typing")

        def fake_is_classvar(hint: Any) -> bool:
            return _get_origin(hint) is _ClassVar

        fake_typing.is_classvar = fake_is_classvar  # type: ignore[attr-defined]

        # Patch environment to simulate pydantic v1
        monkeypatch.setattr(_pyd, "VERSION", "1.10.13", raising=False)
        monkeypatch.setitem(sys.modules, "pydantic.typing", fake_typing)

        # Reload module to execute import branch for v1
        cd = importlib.reload(cd)

        # Assert that is_classvar was imported from our injected module and behaves correctly
        injected = sys.modules["pydantic.typing"]
        assert cd.is_classvar is getattr(injected, "is_classvar")
        assert cd.is_classvar(_ClassVar[int]) is True
        assert cd.is_classvar(int) is False

        # Restore original state and reload back
        monkeypatch.setattr(_pyd, "VERSION", original_version, raising=False)
        # Remove our fake module if it shouldn't exist
        monkeypatch.delitem(sys.modules, "pydantic.typing", raising=False)
        importlib.reload(cd)

    @pytest.mark.it("✅  Should convert snake_case to title case correctly")
    def test_convert_to_title_case(self) -> None:
        assert _convert_to_title_case("get_user_by_id") == "Get User By Id"
        assert _convert_to_title_case("create") == "Create"
        assert _convert_to_title_case("list_all_items") == "List All Items"
        assert _convert_to_title_case("update_user_profile") == "Update User Profile"

    @pytest.mark.it("✅  Should set route summary based on function name when not provided")
    def test_route_summary_default_from_function_name(self, router: APIRouter) -> None:
        @controller(router)
        class Controller:
            @router.get("/items")
            def get_all_items(self) -> str:
                return "items"

        matching = [
            r for r in router.routes if hasattr(r, "path") and getattr(r, "path", "") == "/items"
        ]
        assert len(matching) == 1
        assert matching[0].summary == "Get All Items"

    @pytest.mark.it("✅  Should preserve explicit summary when provided")
    def test_route_summary_explicit_preserved(self, router: APIRouter) -> None:
        @controller(router)
        class Controller:
            @router.get("/users", summary="Custom Summary For Users")
            def get_users(self) -> str:
                return "users"

        matching = [
            r for r in router.routes if hasattr(r, "path") and getattr(r, "path", "") == "/users"
        ]
        assert len(matching) == 1
        assert matching[0].summary == "Custom Summary For Users"

    @pytest.mark.it("✅  Should skip summary update for non-APIRoute routes")
    def test_update_route_summary_skips_non_api_route(self) -> None:
        from starlette.routing import Route

        def dummy_endpoint() -> None:
            pass

        route = Route("/dummy", dummy_endpoint)
        _update_route_summary(route)
        assert not hasattr(route, "summary")
