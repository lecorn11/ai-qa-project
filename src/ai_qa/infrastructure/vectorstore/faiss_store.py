from typing import Optional
import faiss
import numpy as np

from ai_qa.domain.ports import VectorStorePort, EmbeddingPort
from ai_qa.domain.entities import DocumentChunk

class FaissVectorStore(VectorStorePort):
    """FAISS 向量存储实现"""

    def __init__(self, embedding: EmbeddingPort, dimension: int = 1024):
        """
        Args:
            embedding: 向量化服务
            dimension: 向量维度（text-embedding-v3 默认是1024
        """
        self._embedding = embedding
        self._dimension = dimension

        # 创建 FAISS 索引（使用 L2 距离）
        self._index = faiss.IndexFlatL2(dimension)

        # 存储原始文档块（FAISS 只存向量，我们需要额外存储文本）
        self._chunks : list[DocumentChunk] = []

    def add_documents(self, chunks: list[DocumentChunk]) -> None:
        """添加文档块到向量存储"""
        if not chunks:
            return 
        
        # 提取文本内容
        texts = [chunk.content for chunk in chunks]

        # 向量化
        vectors = self._embedding.embed_texts(texts)

        # 转换为 numpy 数组
        vectors_np = np.array(vectors, dtype=np.float32)

        # 添加到 FAISS 索引
        self._index.add(vectors_np)

        # 保存原始文档块
        self._chunks.extend(chunks)

    def search(self, query, top_k = 3):
        """搜索相关文档块"""
        if self._index.ntotal == 0:
            return []
        
        # 向量化查询
        query_vector = self._embedding.embed_query(query)
        query_np = np.array([query_vector], dtype=np.float32)

        # 搜索最相似的 top_k 个向量
        distances, indices = self._index.search(query_np,min(top_k, self._index.ntotal))

        # 返回对应的文档块
        results = []
        for idx in indices[0]:
            if idx >= 0 and idx < len(self._chunks):
                results.append(self._chunks[idx])
        
        return results

    def clear(self):
        """清空向量存储"""
        self._index = faiss.IndexFlatL2(self._dimension)
        self._chunks = []

    @property
    def count(self) -> int:
        """返回存储的文档块数量"""
        return len(self._chunks)
