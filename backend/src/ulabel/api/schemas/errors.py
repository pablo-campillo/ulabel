from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str = Field(..., description="Machine-readable error code.", examples=["PROJECT_NOT_FOUND"])
    message: str = Field(..., description="Human-readable error message.", examples=["Project not found"])
    details: list = Field(default_factory=list, description="Additional error details.")


class ErrorResponse(BaseModel):
    error: ErrorBody
