"""Router for authentication endpoints.

Provides a simple sign-in endpoint that authenticates users by
username and returns their identity and role.
"""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from ulabel.api.schemas.tokens import Claim, LoginRequest
from ulabel.application.login import LoginUseCase
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
            "content": {"application/json": {"example": {"error": {"code": "USER_NOT_FOUND", "message": "User not found", "details": []}}}},
        },
    },
)
@inject
async def login(
    request: LoginRequest,
    use_case: LoginUseCase = Depends(Provide[Container.login_use_case]),
):
    """Authenticate a user by username and return their claim.

    Args:
        request: Contains the username to authenticate.
        use_case: Injected login use case.

    Returns:
        A Claim with the user's ID, username, and role.
    """
    user = await use_case.execute(request.username)
    return Claim(username=user.username, id=user.id, role=user.role)
