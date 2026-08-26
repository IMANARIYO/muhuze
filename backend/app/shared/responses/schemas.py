from typing import Literal

from pydantic import BaseModel


class APIResponse[T](BaseModel):
    status: Literal["success", "error"]
    message: str
    data: T | None = None
