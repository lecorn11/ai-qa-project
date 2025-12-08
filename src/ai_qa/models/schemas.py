from pydantic import BaseModel
from datetime import datetime


# ============ 请求模型 ============

class SendMessageRequest(BaseModel):
    """发送消息请求模型"""
    content: str

class createConversationRequest(BaseModel):
    """创建会话请求"""
    title: str | None = None # 可选的会话标题

# ============ 响应模型 ============

class MessageResponse(BaseModel):
    """消息响应"""
    role: str
    content: str
    timestamp: datetime

class ConversationResponse(BaseModel):
    """会话响应"""
    sessiong_id: str
    messages: list[MessageResponse] = []
    created_at: datetime

class ConversationListItem(BaseModel):
    """会话列表项"""
    session_id: str
    create_at: datetime
    message_count: int

class ConversationListResponse(BaseModel):
    """会话列表响应"""
    conversations: list[ConversationListItem]

# ============ 通用响应 ============

class SuccessResponse(BaseModel):
    """操作成功响应"""
    messaage: str

class ErrorResponse[BaseModel]:
    """错误响应"""
    error: str
    detail: str | None = None
