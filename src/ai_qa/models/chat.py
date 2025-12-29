from datetime import datetime
from pydantic import BaseModel, Field


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    content: str = Field(..., description="消息内容", examples=["你好，请介绍一下 Python"])
    knowledge_base_id: str | None = Field(None, description="知识库 ID（使用知识库时必填）")
    use_knowledge: bool = Field(False, description="是否使用知识库回答")


class MessageResponse(BaseModel):
    """消息响应"""
    role: str = Field(..., description="角色：user/assistant", examples=["assistant"])
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(..., description="时间戳")


class ConversationResponse(BaseModel):
    """会话响应"""
    session_id: str = Field(..., description="会话 ID")
    title: str = Field(..., description="会话标题")
    created_at: datetime | None = Field(None, description="创建时间")
    updated_at: datetime | None = Field(None, description="更新时间")


class ConversationListResponse(BaseModel):
    """会话列表响应"""
    conversations: list[ConversationResponse]