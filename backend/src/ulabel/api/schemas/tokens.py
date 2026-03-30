"""Pydantic schemas for authentication requests and responses."""

from uuid import UUID

from pydantic import BaseModel, Field

from ulabel.domain.users import UserRole


class LoginRequest(BaseModel):
    """Request body for user sign-in by username."""
    username: str = Field(..., description="Username registered in the system.")

    model_config = {
        "json_schema_extra": {
            "example": {"username": "john_doe"}
        }
    }


class Claim(BaseModel):
    """Response body containing the authenticated user's identity and role."""

    username: str = Field(..., description="Username.")
    id: UUID = Field(..., description="Unique user identifier.")
    role: UserRole = Field(..., description="User role: `admin` or `labeler`.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "john_doe",
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "role": "admin",
            }
        }
    }
