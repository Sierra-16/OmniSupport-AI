from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.services.auth_service import register_user, authenticate_user
from app.middleware.auth import decode_token, oauth2_scheme

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await register_user(db, req.name, req.phone, req.password, req.email)
    token_data = await authenticate_user(db, req.phone, req.password)
    return token_data


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    token_data = await authenticate_user(db, req.phone, req.password)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="手机号或密码错误")
    return token_data


@router.get("/me")
async def get_me(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    return {"user_id": int(payload["sub"]), "role": payload["role"]}
