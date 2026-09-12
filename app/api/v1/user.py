from datetime import datetime

from fastapi import APIRouter

from app.schemas.user import UserCreate, UserCreateResponse, UserResponse

router = APIRouter(prefix="/user", tags=["user"])


@router.post('/create', response_model=UserCreateResponse, status_code=201)
async def create_user(user: UserCreate) -> UserCreateResponse:
    created_user = UserResponse(
        id=0,
        name=user.name,
        email=user.email,
        password_hash="hashed",
        is_active=True,
        created_at=datetime.now(),
    )

    return {
        "code": 201,
        "success": True,
        "message": "User created successfully",
        "user": created_user,
    }
    