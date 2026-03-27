from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from ulabel.api.schemas.tokens import Claim, LoginRequest
from ulabel.application.login import LoginUseCase, UserNotFound
from ulabel.container import Container

router = APIRouter()


@router.post(
    "",
    response_model=Claim,
    summary="Sign in",
    description="""
Authenticates a user by username and returns their session information (ID and role).

> **Note:** no password is required. The system assumes the username is unique
> and was pre-created in the database.
""",
    responses={
        200: {"description": "Sign-in successful. Returns the user's ID and role."},
        404: {
            "description": "User not found.",
            "content": {"application/json": {"example": {"detail": "User not found"}}},
        },
    },
)
@inject
async def login(
    request: LoginRequest,
    use_case: LoginUseCase = Depends(Provide[Container.login_use_case]),
):
    try:
        user = await use_case.execute(request.username)
    except UserNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return Claim(username=user.username, id=user.id, role=user.role)
