from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int = Field(..., description="Total number of records.")
    limit: int = Field(..., description="Maximum items per page.")
    offset: int = Field(..., description="Number of items skipped.")
