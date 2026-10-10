import json
from decimal import Decimal

import pytest
from pydantic import BaseModel

from app.shared.responses.api_response import error_response, success_response


class Item(BaseModel):
    name: str
    price: Decimal


def body_of(response) -> dict:
    return json.loads(response.body)


def test_success_response_envelope() -> None:
    response = success_response(data={"id": 1}, message="Created", status_code=201)
    assert response.status_code == 201
    assert body_of(response) == {
        "success": True,
        "data": {"id": 1},
        "message": "Created",
        "status_code": 201,
    }


def test_success_response_defaults() -> None:
    response = success_response()
    assert response.status_code == 200
    assert body_of(response) == {
        "success": True,
        "data": None,
        "message": "Request successful",
        "status_code": 200,
    }


def test_nested_models_serialize_and_money_stays_exact() -> None:
    response = success_response(data=[Item(name="Phone", price=Decimal("100000.10"))])
    assert body_of(response)["data"] == [{"name": "Phone", "price": "100000.10"}]


@pytest.mark.parametrize("status_code", [204, 301, 400, 500])
def test_success_response_rejects_non_body_2xx_statuses(status_code: int) -> None:
    with pytest.raises(ValueError):
        success_response(status_code=status_code)


def test_error_response_envelope() -> None:
    response = error_response("Product not found", 404)
    assert response.status_code == 404
    assert body_of(response) == {
        "success": False,
        "data": None,
        "message": "Product not found",
        "status_code": 404,
    }


def test_error_response_keeps_headers() -> None:
    response = error_response("Method Not Allowed", 405, headers={"Allow": "GET"})
    assert response.headers["allow"] == "GET"
