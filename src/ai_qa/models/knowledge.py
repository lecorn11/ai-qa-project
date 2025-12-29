from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CreateKnowledgeBaseRequest(BaseModel):
    """创建知识库请求"""
    name: str = Field(..., min_length=1, max_length=100, description="知识库名称", examples=["Python 学习资料"])
    description: str | None = Field(None, description="知识库描述")


class UpdateKnowledgeBaseRequest(BaseModel):
    """更新知识库请求"""
    name: str | None = Field(None, description="知识库名称")
    description: str | None = Field(None, description="知识库描述")


class AddDocumentRequest(BaseModel):
    """添加文档请求"""
    content: str = Field(..., description="文档内容")
    title: str | None = Field(None, description="文档标题", examples=["Python 基础教程"])


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: str = Field(..., description="知识库 ID")
    name: str = Field(..., description="知识库名称")
    description: str | None = Field(None, description="知识库描述")
    document_count: int = Field(0, description="文档数量")
    chunk_count: int = Field(0, description="文档块数量")
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class KnowledgeBaseListResponse(BaseModel):
    """知识库列表响应"""
    knowledge_bases: list[KnowledgeBaseResponse]


class KnowledgeBaseStatus(BaseModel):
    """知识库状态"""
    name: str | None = Field(None, description="知识库名称")
    document_count: int = Field(..., description="文档块数量")
    is_ready: bool = Field(..., description="是否可用")