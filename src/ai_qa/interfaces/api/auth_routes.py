from fastapi import APIRouter, Depends, HTTPException
from psycopg2 import IntegrityError
from pydantic import BaseModel, ConfigDict, EmailStr

from ai_qa.domain.exceptions import ConflictException
from ai_qa.interfaces.api.dependencies import get_user_service, get_current_user
from ai_qa.infrastructure.database.models import User
from ai_qa.application.user_service import UserService
from ai_qa.models import RegisterRequest, LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post(
        "/register", 
        response_model=UserResponse,
        summary="用户注册",
        responses={
            409: {"description": "用户名或邮箱已存在"}
        })
async def register(
    request: RegisterRequest, 
    user_service: UserService = Depends(get_user_service)
) -> User:
    """
    注册新用户账号。
    
    - **username**: 用户名，2-50 字符，不可重复
    - **password**: 密码，至少 6 位
    - **email**: 邮箱，可选，不可重复
    """
    try:
        user = user_service.resigter(
            username=request.username, 
            password=request.password, 
            email=request.email
        )
        return user
    except Exception as e:
        if "用户名已存在" in str(e) or "邮箱已被注册" in str(e):
            raise ConflictException(str(e))
        raise


@router.post(
        "/login", 
        response_model=TokenResponse,
        summary="用户登录",
        responses={
            401: {"description": "用户名或密码错误"},
            403: {"description": "账号已被禁用"}
        })
async def login(
    request: LoginRequest, 
    user_service: UserService = Depends(get_user_service)
):
    """
    用户登录，获取 JWT Token。
    
    登录成功后，在后续请求的 Header 中携带：
```
    Authorization: Bearer {access_token}
```
    """
    user, token = user_service.login(
        username=request.username, password=request.password
    )
    return TokenResponse(access_token=token)

@router.get(
    "/me",
    response_model=UserResponse,
    summary="获取当前用户",
    responses={
        401: {"description": "未登录或 Token 无效"}
    }
)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户的信息。
    
    需要在请求头中携带有效的 JWT Token。
    """
    return current_user
