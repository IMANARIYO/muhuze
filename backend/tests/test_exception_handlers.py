import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.shared.exceptions.base import NotFoundError
from app.shared.exceptions.handlers import register_exception_handlers


def build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom/app-error")
    async def raise_app_error():
        raise NotFoundError("Widget not found")

    @app.get("/boom/unhandled")
    async def raise_unhandled():
        raise RuntimeError("something exploded")

    @app.get("/boom/validation")
    async def raise_validation(count: int):
        return {"count": count}

    return app


@pytest.fixture
async def error_client() -> AsyncClient:
    transport = ASGITransport(app=build_app(), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_app_error_maps_to_envelope(error_client: AsyncClient) -> None:
    response = await error_client.get("/boom/app-error")
    assert response.status_code == 404
    assert response.json() == {"status": "error", "message": "Widget not found", "data": None}


async def test_unhandled_exception_maps_to_500_envelope(error_client: AsyncClient) -> None:
    response = await error_client.get("/boom/unhandled")
    assert response.status_code == 500
    assert response.json() == {
        "status": "error",
        "message": "Internal server error",
        "data": None,
    }


async def test_validation_error_maps_to_envelope(error_client: AsyncClient) -> None:
    response = await error_client.get("/boom/validation")
    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
    assert body["data"] is None
