
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from ai_qa.infrastructure.database.models import (
    KnowledgeBase as KnowledgeBaseModel,
    Document as DocumentModel,
    DocumentChunk as DocumnetChunkModel
)


class KnowledgeBaseService:
    """知识库管理服务"""

    def __init__(self, db: Session):
        self._db = db

    def create(self, user_id: str, name: str, description: str = None) -> KnowledgeBaseModel:
        """创建知识库"""
        kb =  KnowledgeBaseModel(
            user_id=user_id,
            name=name,
            description=description
        )
        self._db.add(kb)
        self._db.commit()
        self._db.refresh(kb) # 从数据库重新加载
        return kb
    
    def delete(self, kb_id: int, user_id: int) -> bool:
        """删除知识库(软删除)"""
        kb = self.get_by_id(kb_id, user_id)
        if not kb:
            return False
        
        kb.status = -1
        kb.update_at = datetime.now(timezone.utc)
        self._db.commit()
        return True

    def update(self, kb_id: int, user_id: int, name: str = None, description: str = None) -> KnowledgeBaseModel:
        """更新知识库"""
        kb = self.get_by_id(kb_id, user_id)
        if not kb:
            return None
        
        if name:
            kb.name = name
        if description is not None:
            kb.description = description
        kb.update_at = datetime.now(timezone.utc)

        self._db.commit()
        self._db.refresh(kb)

        return kb

    def get_by_id(self, kb_id: int, user_id: int) -> KnowledgeBaseModel | None:
        """获取知识库"""
        return self._db.query(KnowledgeBaseModel).filter(
            KnowledgeBaseModel.id == kb_id,
            KnowledgeBaseModel.user_id == user_id,
            KnowledgeBaseModel.status == 1
        ).first()
    
    def list_by_user(self, user_id: int) -> list[KnowledgeBaseModel]:
        """列出用户的所有知识库"""
        return self._db.query(KnowledgeBaseModel).filter(
            KnowledgeBaseModel.user_id == user_id,
            KnowledgeBaseModel.status == 1
        ).order_by(KnowledgeBaseModel.created_at.desc()).all()
    
    def get_stats(self, kb_id: int, user_id: int) -> dict | None:
        """获取知识库统计信息"""
        kb = self.get_by_id(kb_id, user_id)
        if not kb:
            return None
        
        # 统计文档数
        doc_count = self._db.query(DocumentModel).filter(
            DocumentModel.knowledge_base_id == kb_id,
            DocumentModel.status == 1
        ).count()

        # 统计文档块数量
        chunk_count = self._db.query(DocumnetChunkModel).join(DocumentModel).filter(
            DocumnetChunkModel.document_id == DocumentModel.id,
            DocumentModel.knowledge_base_id == kb_id,            
            DocumentModel.status == 1
        ).count()

        return {
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "document_count": doc_count,
            "chunk_count": chunk_count,
            "created_at": kb.created_at,
            "updated_at": kb.updated_at
        }