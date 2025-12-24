from turtle import update
from pydantic import BaseModel
from datetime import datetime


# ============ 请求模型 ============

class SendMessageRequest(BaseModel):
    """发送消息请求模型"""
    content: str
    use_knowledge: bool = False

class CreateConversationRequest(BaseModel):
    """创建会话请求"""
    title: str | None = None # 可选的会话标题

class AddDocumentRequest(BaseModel):
    """添加文档请求"""
    content: str
    title: str | None = None

# ============ 响应模型 ============

class MessageResponse(BaseModel):
    """消息响应"""
    role: str
    content: str
    timestamp: datetime

class ConversationResponse(BaseModel):
    """会话响应"""
    sessiong_id: int
    # messages: list[MessageResponse] = []
    title: str
    created_at: datetime | None = None
    update_at: datetime | None = None

# class ConversationListItem(BaseModel):
#     """会话列表项"""
#     session_id: str
#     create_at: datetime
#     message_count: int

class ConversationListResponse(BaseModel):
    """会话列表响应"""
    conversations: list[ConversationResponse]

class KnowledgeBaseStatus(BaseModel):
    """知识库状态"""
    name: str | None
    document_count: int
    is_ready: bool

class DocumentInfo(BaseModel):
    """文档信息"""
    title: str
    chunk_count: int
    added_at: datetime

class DocumentListResponse(BaseModel):
    """文档列表响应"""
    documents: list[DocumentInfo]
    total_chunks: int

# ============ 通用响应 ============

class SuccessResponse(BaseModel):
    """操作成功响应"""
    messaage: str

class ErrorResponse[BaseModel]:
    """错误响应"""
    error: str
    detail: str | None = None
