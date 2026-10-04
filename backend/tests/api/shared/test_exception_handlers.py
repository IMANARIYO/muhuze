import logging

import pytest
from fastapi import FastAPI, HTTPException
from httpx import AsyncClient

from app.core.request_context_middleware import REQUEST_ID_HEADER
from app.shared.exceptions.application_exceptions import BusinessRuleError, NotFoundError


@pytest.fixture
def app(app: FastAPI) -> FastAPI:
    @app.get("/test/not-found")
    async def raise_not_found():
        raise NotFoundError("Widget not found")

    @app.get("/test/business-rule")
    async def raise_business_rule():
        raise BusinessRuleError("Insufficient available balance")

    @app.get("/test/http-dict-detail")
    async def raise_http_with_dict_detail():
        raise HTTPException(status_code=403, detail={"internal": "details"})

    @app.get("/test/unhandled")
    async def raise_unhandled():
        raise RuntimeError("database password is hunter2")

    @app.get("/test/validation")
    async def needs_int(count: int, size: int):
        return {"count": count, "size": size}

    return app


async def test_app_error_maps_to_envelope(client: AsyncClient) -> None:
    response = await client.get("/test/not-found")
    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "data": None,
        "message": "Widget not found",
        "status_code": 404,
    }


async def test_business_rule_error_maps_to_422(client: AsyncClient) -> None:
    response = await client.get("/test/business-rule")
    assert response.status_code == 422
    assert response.json()["message"] == "Insufficient available balance"


async def test_unknown_route_uses_envelope(client: AsyncClient) -> None:
    response = await client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "data": None,
        "message": "Not Found",
        "status_code": 404,
    }


async def test_method_not_allowed_keeps_allow_header(client: AsyncClient) -> None:
    response = await client.post("/health")
    assert response.status_code == 405
    assert response.json()["success"] is False
    assert "GET" in response.headers["allow"]


async def test_non_string_http_detail_is_not_leaked(client: AsyncClient) -> None:
    response = await client.get("/test/http-dict-detail")
    assert response.status_code == 403
    assert response.json()["message"] == "Forbidden"


async def test_validation_error_lists_every_invalid_field(client: AsyncClient) -> None:
    response = await client.get("/test/validation", params={"count": "abc"})
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["status_code"] == 422
    assert "count:" in body["message"]
    assert "size:" in body["message"]
    assert "abc" not in body["message"]  # submitted values are never echoed


async def test_unhandled_exception_returns_generic_500_and_is_logged(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.ERROR, logger="app.errors"):
        response = await client.get("/test/unhandled", headers={REQUEST_ID_HEADER: "trace-500"})

    assert response.status_code == 500
    assert response.json() == {
        "success": False,
        "data": None,
        "message": "Internal server error",
        "status_code": 500,
    }
    assert "hunter2" not in response.text
    assert response.headers[REQUEST_ID_HEADER] == "trace-500"

    (record,) = [r for r in caplog.records if r.name == "app.errors"]
    assert record.exc_info is not None
    assert record.path == "/test/unhandled"
