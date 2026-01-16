import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from ai_qa.infrastructure.database.models import (
    KnowledgeBase as KnowledgeBaseModel,
    Document as DocumentModel,
    DocumentChunk as DocumentChunkModel,
)

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """知识库管理服务"""

    def __init__(self, db: Session):
        self._db = db

    def create(
        self, user_id: str, name: str, description: str = None
    ) -> KnowledgeBaseModel:
        """创建知识库"""
        logger.info(
            f"创建知识库开始 user_id={user_id}, name={name}, description={description}"
        )
        kb = KnowledgeBaseModel(user_id=user_id, name=name, description=description)
        self._db.add(kb)
        self._db.commit()
        self._db.refresh(kb)  # 从数据库重新加载
        logger.info(f"创建知识库完成 kb={kb}")
        return kb

    def delete(self, kb_id: str, user_id: str) -> bool:
        """删除知识库(软删除)"""
        logger.info(f"删除知识库开始 kb_id={kb_id}, user_id={user_id}")
        kb = self.get_by_id(kb_id, user_id)
        if not kb:
            logger.info(f"知识库不存在 kb_id={kb_id}")
            return False

        kb.status = -1
        kb.update_at = datetime.now(timezone.utc)
        self._db.commit()
        logger.info(f"删除知识库成功 kb_id={kb_id}, user_id={user_id}")
        return True

    def update(
        self, kb_id: str, user_id: str, name: str = None, description: str = None
    ) -> KnowledgeBaseModel:
        """更新知识库"""
        logger.info(
            f"更新知识库开始 kb_id={kb_id}, user_id={user_id}, name={name}, description={description}"
        )
        kb = self.get_by_id(kb_id, user_id)
        if not kb:
            logger.info(f"知识库不存在 kb_id={kb_id}")
            return None

        if name:
            kb.name = name
        if description is not None:
            kb.description = description
        kb.update_at = datetime.now(timezone.utc)

        self._db.commit()
        self._db.refresh(kb)
        logger.info(f"更新知识库完成 kb={kb}")
        return kb

    def get_by_id(self, kb_id: str, user_id: str) -> KnowledgeBaseModel | None:
        """获取知识库"""
        logger.debug(f"查询知识库开始 kb_id={kb_id}, user_id={user_id}")
        kb = (
            self._db.query(KnowledgeBaseModel)
            .filter(
                KnowledgeBaseModel.id == kb_id,
                KnowledgeBaseModel.user_id == user_id,
                KnowledgeBaseModel.status == 1,
            )
            .first()
        )
        return kb

    def list_by_user(self, user_id: str) -> list[KnowledgeBaseModel]:
        """列出用户的所有知识库"""
        return (
            self._db.query(KnowledgeBaseModel)
            .filter(
                KnowledgeBaseModel.user_id == user_id, KnowledgeBaseModel.status == 1
            )
            .order_by(KnowledgeBaseModel.created_at.desc())
            .all()
        )

    def get_stats(self, kb_id: str, user_id: str) -> dict | None:
        """获取知识库统计信息"""
        kb = self.get_by_id(kb_id, user_id)
        if not kb:
            return None

        # 统计文档数
        doc_count = (
            self._db.query(DocumentModel)
            .filter(DocumentModel.knowledge_base_id == kb_id, DocumentModel.status == 1)
            .count()
        )

        # 统计文档块数量
        chunk_count = (
            self._db.query(DocumentChunkModel)
            .join(DocumentModel)
            .filter(
                DocumentChunkModel.document_id == DocumentModel.id,
                DocumentModel.knowledge_base_id == kb_id,
                DocumentModel.status == 1,
            )
            .count()
        )

        return {
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "document_count": doc_count,
            "chunk_count": chunk_count,
            "created_at": kb.created_at,
            "updated_at": kb.updated_at,
        }
