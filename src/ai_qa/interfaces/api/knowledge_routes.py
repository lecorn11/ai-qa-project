from turtle import title
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from ai_qa.application.knowledge_service import KnowledgeService
from ai_qa.interfaces.api.dependecnies import get_knowledge_service
from ai_qa.models.schemas import AddDocumentRequest, KnowledgeBaseStatus, SuccessResponse

router = APIRouter(prefix="/knowledge",tags=["知识库"])

# 存储文档信息（简化实现）
_documents: list[dict] = []

@router.get("/status", response_model=KnowledgeBaseStatus)
async def get_knowledge_base_status(
    knowledge_serivce: KnowledgeService = Depends(get_knowledge_service)
):
    """获取知识库状态"""
    kb = knowledge_serivce._knowledge_base

    return KnowledgeBaseStatus(
        name=kb.name if kb else None,
        document_count=knowledge_serivce.chunk_count,
        is_ready=knowledge_serivce.chunk_count > 0
    )

@router.post("/documents",response_model=SuccessResponse)
async def add_document(
    request: AddDocumentRequest,
    knowledge_serivce: KnowledgeService = Depends(get_knowledge_service)
):
    """添加文档到知识库"""

    # 如果知识库还没有创建，则先创建
    if knowledge_serivce._knowledge_base is None:
        knowledge_serivce.create_knowledge_base(name="默认知识库")
    
    import os, dashscope
    print("DASHSCOPE_API_BASE =", os.getenv("DASHSCOPE_API_BASE"))
    print("dashscope.base_http_api_url =", getattr(dashscope, "base_http_api_url", None))

    # 添加文档
    chunk_count = knowledge_serivce.add_text(
        text = request.content,
        metadata= request.title or "未命名文档"
    )

    # 记录文档信息
    _documents.append({
        "title": request.title or "未命名文档",
        "chunk_count": chunk_count,
        "added_at": datetime.now()
    })

    return SuccessResponse(messaage=f"文档已添加。共切分为 {chunk_count} 个文档块")

@router.get("/documents")
async def list_documents(
    knowledge_serivce: KnowledgeService = Depends(get_knowledge_service)
):
    """获取已添加的文档列表"""
    return {
        "documents": _documents,
        "total_chunks":knowledge_serivce.chunk_count
    }

@router.delete("/documents")
async def clear_documents(
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """清空知识库"""
    knowledge_service._vector_store.clear()
    _documents.clear()

    return SuccessResponse(messaage="知识库已清空")

