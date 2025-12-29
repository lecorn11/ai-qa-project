from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名", examples=["alice"])
    password: str = Field(..., min_length=6, description="密码", examples=["123456"])
    email: str | None = Field(None, description="邮箱（可选）", examples=["alice@example.com"])


class LoginRequest(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名", examples=["alice"])
    password: str = Field(..., description="密码", examples=["123456"])


class TokenResponse(BaseModel):
    """登录成功响应"""
    access_token: str = Field(..., description="JWT Token", examples=["eyJhbGciOiJIUzI1NiIs..."])
    token_type: str = Field(default="bearer", description="Token 类型")


class UserResponse(BaseModel):
    """用户信息响应"""
    id: str = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    email: str | None = Field(None, description="邮箱")
    nickname: str | None = Field(None, description="昵称")
    status: int = Field(..., description="状态：1-正常，-1-禁用")

    model_config = ConfigDict(from_attributes=True)