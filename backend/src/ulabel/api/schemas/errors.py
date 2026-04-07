"""Pydantic schemas for structured API error responses."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    """Inner error object containing code, message, and details."""

    code: str = Field(
        ...,
        description="Machine-readable error code.",
        examples=["PROJECT_NOT_FOUND"],
    )
    message: str = Field(
        ...,
        description="Human-readable error message.",
        examples=["Project not found"],
    )
    details: list[Any] = Field(default_factory=list, description="Additional error details.")


class ErrorResponse(BaseModel):
    """Wrapper schema for API error responses."""

    error: ErrorBody
