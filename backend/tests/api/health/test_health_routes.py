from httpx import AsyncClient


async def test_health_returns_standard_envelope(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "data": {"status": "ok"},
        "message": "Service is healthy",
        "status_code": 200,
    }


async def test_openapi_documents_the_envelope(client: AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()
    response_schema = schema["paths"]["/health"]["get"]["responses"]["200"]
    ref = response_schema["content"]["application/json"]["schema"]["$ref"]
    envelope = schema["components"]["schemas"][ref.rsplit("/", 1)[-1]]
    assert set(envelope["properties"]) == {"success", "data", "message", "status_code"}
