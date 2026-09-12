from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import DataError, IntegrityError

from app.models.user import User
from app.schemas.user import UserCreate, UserCreateResponse, UserLogin, UserResponse, UserUpdate
from app.config.database import get_db
from app.utils.helpers import _generate_email_code, _hash_password, _verify_password
from app.services.smtp_email import send_email as smtp_email_sender
router = APIRouter(prefix="/user", tags=["user"])


@router.post('/login', response_model=UserResponse)
async def login_user(user_data: UserLogin, db: AsyncSession = Depends(get_db)) -> User:
    user = await db.scalar(select(User).where(User.email == user_data.email))
    if user is None or not _verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    return user


@router.get('/get/{user_id}', response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)) -> User:
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user


@router.patch('/patch/{user_id}', response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    user.name = user_data.name
    await db.commit()
    await db.refresh(user)
    return user


@router.delete('/delete/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)) -> None:
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    await db.delete(user)
    await db.commit()

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
