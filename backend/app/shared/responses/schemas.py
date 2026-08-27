from typing import Literal

from pydantic import BaseModel, Field


class APIResponse[T](BaseModel):
    status: Literal["success", "error"] = Field(
        description="Response status: 'success' or 'error'"
    )
    message: str = Field(description="Human-readable status message")
    data: T | None = Field(default=None, description="Response payload (null on errors)")
