"""Generic pagination wrapper for domain query results."""

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class PaginatedResult(Generic[T]):
    """A page of results together with the total count.

    Attributes:
        items: The items in the current page.
        total: The total number of items across all pages.
    """

    items: list[T]
    total: int
