import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User
from app.middleware.auth import create_token


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


async def register_user(db: AsyncSession, name: str, phone: str, password: str, email: str | None = None) -> User:
    user = User(
        name=name,
        phone=phone,
        email=email,
        password_hash=hash_password(password),
        role="user",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, phone: str, password: str) -> dict | None:
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return None
    token = create_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer", "user_id": user.id, "name": user.name, "role": user.role}


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
