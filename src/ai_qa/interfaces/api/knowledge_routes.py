from fastapi import APIRouter, Depends, UploadFile, File

from ai_qa.application.knowledge_base_service import KnowledgeBaseService
from ai_qa.application.knowledge_service import KnowledgeService
from ai_qa.domain.exceptions import NotFoundException, ValidationException
from ai_qa.infrastructure.database.models import User
from ai_qa.infrastructure.document.pdf_reader import extract_text_from_pdf
from ai_qa.interfaces.api.dependencies import get_current_user, get_knowledge_base_service, get_knowledge_service
from ai_qa.models import (
    CreateKnowledgeBaseRequest,
    UpdateKnowledgeBaseRequest,
    AddDocumentRequest,
    KnowledgeBaseResponse,
    KnowledgeBaseListResponse,
    KnowledgeBaseStatus,
    SuccessResponse,
)

router = APIRouter(tags=["知识库"])

# 存储文档信息（简化实现）
_documents: list[dict] = []

# ============ 知识库管理 API ============

@router.post(
    "/knowledge-bases",
    response_model=KnowledgeBaseResponse,
    summary="创建知识库",
    responses={
        401: {"description": "未登录或 Token 无效"}
    }
)
async def create_knowledge_base(
    request: CreateKnowledgeBaseRequest,
    current_user: User = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service)
):
    """
    创建一个新的知识库。
    
    创建后可以上传文档到该知识库，用于 RAG 问答。
    """
    kb = kb_service.create(
        user_id=current_user.id,
        name=request.name,
        description=request.description
    )
    return KnowledgeBaseResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        created_at=kb.created_at,
        updated_at=kb.updated_at
    )

@router.get(
    "/knowledge-bases",
    response_model=KnowledgeBaseListResponse,
    summary="获取知识库列表",
    responses={
        401: {"description": "未登录或 Token 无效"}
    }
)
async def list_knowledge_bases(
    current_user: User = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service)
):
    """获取当前用户的所有知识库。"""
    kbs = kb_service.list_by_user(current_user.id)

    result = []
    for kb in kbs:
        stats = kb_service.get_stats(kb.id, current_user.id)
        result.append(KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            document_count=stats["document_count"] if stats else 0,
            chunk_count=stats["chunk_count"] if stats else 0,
            created_at=kb.created_at,
            updated_at=kb.updated_at
        ))
    return KnowledgeBaseListResponse(knowledge_bases=result)

@router.get(
    "/knowledge-bases/{kb_id}",
    response_model=KnowledgeBaseResponse,
    summary="获取知识库详情",
    responses={
        401: {"description": "未登录或 Token 无效"},
        404: {"description": "知识库不存在"}
    }
)
async def get_knowledge_base(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service)
):
    """获取指定知识库的详细信息，包括文档数量统计。"""
    stats = kb_service.get_stats(kb_id, current_user.id)
    if not stats:
        raise NotFoundException(resource="知识库")
    
    return KnowledgeBaseResponse(**stats)


@router.put(
    "/knowledge-bases/{kb_id}",
    response_model=KnowledgeBaseResponse,
    summary="更新知识库",
    responses={
        401: {"description": "未登录或 Token 无效"},
        404: {"description": "知识库不存在"}
    }
)
async def update_knowledge_base(
    kb_id: str,
    request: UpdateKnowledgeBaseRequest,
    current_user: User = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service)
):
    """更新知识库的名称或描述。"""
    kb = kb_service.update(
        kb_id=kb_id,
        user_id=current_user.id,
        name=request.name,
        description=request.description
    )
    if not kb:
        raise NotFoundException(resource="知识库")
    
    stats = kb_service.get_stats(kb_id, current_user.id)
    return KnowledgeBaseResponse(**stats)


@router.delete(
    "/knowledge-bases/{kb_id}",
    response_model=SuccessResponse,
    summary="删除知识库",
    responses={
        401: {"description": "未登录或 Token 无效"},
        404: {"description": "知识库不存在"}
    }
)
async def delete_knowledge_base(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service)
):
    """删除指定的知识库。"""
    success = kb_service.delete(kb_id, current_user.id)
    if not success:
        raise NotFoundException(resource="知识库")
    
    return SuccessResponse(message="知识库已删除")

@router.get(
    "/knowledge-bases/{kb_id}/status",
    response_model=KnowledgeBaseStatus,
    summary="获取知识库状态",
    responses={
        401: {"description": "未登录或 Token 无效"},
        404: {"description": "知识库不存在"}
    }
)
async def get_knowledge_base_status(
    knowledge_serivce: KnowledgeService = Depends(get_knowledge_service)
):
    """获取知识库的状态信息，包括是否可用于问答。"""
    kb = knowledge_serivce._knowledge_base

    return KnowledgeBaseStatus(
        name=kb.name if kb else None,
        document_count=knowledge_serivce.chunk_count,
        is_ready=knowledge_serivce.chunk_count > 0
    )

# ============ 文档管理 ============

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

    return SuccessResponse(message="知识库已清空")


@router.post(
    "/knowledge-bases/{kb_id}/documents/text",
    response_model=SuccessResponse,
    summary="添加文本文档",
    responses={
        401: {"description": "未登录或 Token 无效"},
        404: {"description": "知识库不存在"}
    }
)
async def add_document(
    kb_id: str,
    request: AddDocumentRequest,
    current_user: User = Depends(get_current_user),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service),
):
    """添加文本到知识库"""

    # 验证知识库归属
    kb = kb_service.get_by_id(kb_id, current_user.id)
    if not kb:
        raise NotFoundException(resource="知识库")

    # 添加到知识库
    chunk_count = knowledge_service.add_document(
        knowledge_base_id=kb_id,
        title=request.title,
        content=request.content,
        file_type="text"
    )

    return SuccessResponse(message=f"文档已添加。共切分为 {chunk_count} 个文档块")


@router.post(
    "/knowledge-bases/{kb_id}/documents/upload",
    response_model=SuccessResponse,
    summary="上传文件",
    responses={
        400: {"description": "文件类型不支持或内容为空"},
        401: {"description": "未登录或 Token 无效"},
        404: {"description": "知识库不存在"}
    }
)
async def upload_document(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service),
):
    """
    上传文件到知识库。
    
    - 支持格式：**PDF**、**TXT**
    - 文件会自动解析、切分并向量化存储
    """

    # 验证知识库归属
    kb = kb_service.get_by_id(kb_id, current_user.id)
    if not kb:
        raise NotFoundException(resource="知识库")
    
    # 检查文件类型
    filename = file.filename.lower()
    if not (filename.endswith(".pdf") or filename.endswith(".txt")):
        raise ValidationException("只支持 PDF 和 TXT 文件")
    
    # 读取文件内容
    content = await file.read()

    # 根据类型提取文本
    if filename.endswith(".pdf"):
        try:
            text = extract_text_from_pdf(content)
        except Exception as e:
            raise ValidationException(f"PDF 解析失败：{str(e)}")
    else:
        # TXT 文件
        text = content.decode("utf-8")
    
    if not text.strip():
        raise ValidationException("文件内容为空")
    
    # 确保知识库已创建
    # if knowledge_service._knowledge_base is None:
    #     knowledge_service.create_knowledge_base(name="默认知识库")
    
    # # 添加到知识库
    # chunk_count = knowledge_service.add_text(
    #     text=text,
    #     metadata={"title": file.filename, "type":"file"}
    # )
    
    # _documents.append({
    #     "title": file.filename,
    #     "type": "pdf" if filename.endswith(".pdf") else "txt",
    #     "chunk_count": chunk_count,
    #     "added_at": datetime.now().isoformat()
    # })

    # 添加到知识库
    chunk_count = knowledge_service.add_document(
        knowledge_base_id=kb_id,
        title=file.filename,
        content=text,
        file_type="pdf" if filename.endswith(".pdf") else "txt",
        file_size=len(content)
    )

    return SuccessResponse(
        message=f"文件 '{file.filename}' 已添加，共切分为{chunk_count} 个文档块"
    )

