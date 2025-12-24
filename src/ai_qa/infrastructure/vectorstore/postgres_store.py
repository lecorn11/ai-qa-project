from sqlalchemy.orm import Session

from ai_qa.domain.entities import DocumentChunk
from ai_qa.domain.ports import VectorStorePort, EmbeddingPort
from ai_qa.infrastructure import embedding
from ai_qa.infrastructure.database.models import (
    DocumentChunk as DocumentChunkModel,
    Document as DocumentModel
)

class PostgresVectorStore(VectorStorePort):
    """基于 PostgreSQL + pgvector 的向量存储"""

    def __init__(self, db: Session, embedding: EmbeddingPort):
        """
        Args:
            db: 数据库会话
            embedding: 向量化服务
        """
        self._db = db
        self._embedding = embedding

    def add_documents(self, chunks: list[DocumentChunk], knowledge_base_id: int = None) -> None:
        """添加文档块到向量存储"""
        if not chunks:
            return
        
        # 批量向量化
        texts = [chunk.content for chunk in chunks]
        embeddings = self._embedding.embed_texts(texts)

        # 批量构建 文档块数据库模型
        chunk_models = [
            DocumentChunkModel(
                document_id = chunk.chunk_id,
                content = chunk.content,
                metadata = chunk.metadata,
                embedding = vector,
                chunk_index = chunk.chunk_id
            )
            for chunk, vector in zip(chunks, embeddings)
        ]

        # 批量插入到数据库
        self._db.add_all(chunk_models)
        self._db.commit()

    def search(self, query: str, knowledge_base_id: int = None, top_k: int = 3) -> list[DocumentChunk]:
        """搜索相关文档块"""
        # 把查询文本向量化
        query_embedding = self._embedding.embed_query(query)

        # 构建查询
        query_obj = self._db.query(DocumentChunkModel)

        # 如果指定了知识库，进行过滤
        if knowledge_base_id is not None:
            query_obj = query_obj.join(DocumentModel).filter(DocumentModel.knowledge_base_id == knowledge_base_id)

        # 使用 pgvector 的 L2 距离排序，然后限制结果数量为 top_k
        query_obj = query_obj.order_by(
            DocumentChunkModel.embedding.l2_distance(query_embedding)
        ).limit(top_k)

        # 返回对应的文档块
        db_chunks = query_obj.all()

        # 转换为领域实体
        results = [
            DocumentChunk(
                chunk_id = db_chunk.id,
                content = db_chunk.content,
                metadata = db_chunk.metadata
            )
            for db_chunk in db_chunks
        ]
 
        return results

    def clear(self, knowledge_base_id: int = None) -> None:
        """清空向量存储"""
        if knowledge_base_id is not None:
            # 删除指定知识库的文档快
            self._db.query(DocumentChunkModel).filter(
                DocumentChunkModel.document_id.in_(
                    self._db.query(DocumentModel.id).filter(
                        DocumentModel.knowledge_base_id == knowledge_base_id
                    )
                )
            ).delete(synchronize_session=False)
        else:
            # 删除所有文档块
            self._db.query(DocumentChunkModel).delete(synchronize_session=False)

    def count(self, knowledge_base_id: int = None) -> int:
        """返回文档块数量"""
        query = self._db.query(DocumentChunkModel)
        if knowledge_base_id is not None:
            query = query.join(DocumentModel).filter(DocumentModel.knowledge_base_id == knowledge_base_id)
        return query.count()