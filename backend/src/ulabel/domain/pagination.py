from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class PaginatedResult(Generic[T]):
    items: list[T]
    total: int
