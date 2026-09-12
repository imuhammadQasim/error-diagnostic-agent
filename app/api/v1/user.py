from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import DataError, IntegrityError

from app.models.user import User
from app.schemas.user import UserCreate, UserCreateResponse, UserResponse
from app.config.database import get_db
from app.utils.helpers import _hash_password, _generate_email_code
from app.services.smtp_email import send_email as smtp_email_sender
router = APIRouter(prefix="/user", tags=["user"])

@router.post('/create', response_model=UserCreateResponse, status_code=201)
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)) -> UserCreateResponse:
    existing_user = await db.scalar(select(User).where(User.email == user_data.email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )
    
    otpcode = _generate_email_code()
    db_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=_hash_password(user_data.password),
        code=otpcode,
        is_active=False,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(db_user)
    
    try:
        await db.commit()
        await db.refresh(db_user)
        await smtp_email_sender(user_data.email, 'Verification account code', otpcode)
        print('email sent successfully ====>>')
    except (IntegrityError, DataError) as exc:
        await db.rollback()
        message = str(exc).lower()
        if "users_email_key" in message or "duplicate" in message or "already exists" in message:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database validation error while creating user.",
        ) from exc

    return {
        "code": 201,
        "success": True,
        "message": "User created successfully",
        "user": db_user,
    }
