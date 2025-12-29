from pydantic import BaseModel, Field

class SuccessResponse(BaseModel):
    """操作成功响应"""
    message: str = Field(..., description="成功信息", examples=["操作成功"])

class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str = Field(..., description="错误信息", examples=["资源不存在"])