from fastapi import APIRouter, Depends, HTTPException
from psycopg2 import IntegrityError
from pydantic import BaseModel, ConfigDict, EmailStr

from ai_qa.domain.exceptions import ConflictException
from ai_qa.interfaces.api.dependecnies import get_user_service, get_current_user
from ai_qa.infrastructure.database.models import User
from ai_qa.application.user_service import UserService

router = APIRouter(prefix="/auth", tags=["认证"])

# ============ 请求/响应模型 ============
class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str | None = None

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    username: str
    email: str | None
    nickname: str | None
    status: int

    model_config = ConfigDict(from_attributes=True)

# ============ 路由处理函数 ============
@router.post("/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    user_service: UserService = Depends(get_user_service)
) -> User:
    """用户注册"""
    try:
        user = user_service.resigter(
            username=request.username,
            password=request.password,
            email=request.email
        )
        return user
    except IntegrityError:
        raise ConflictException("用户名已存在")
    

@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    user_service: UserService = Depends(get_user_service)
):
    """用户登录"""
    user, token = user_service.login(
        username=request.username,
        password=request.password
    )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user