import os
import pickle
import faiss
import numpy as np

from ai_qa.domain.ports import VectorStorePort, EmbeddingPort
from ai_qa.domain.entities import DocumentChunk

class FaissVectorStore(VectorStorePort):
    """FAISS 向量存储实现"""

    def __init__(
            self, 
            embedding: EmbeddingPort, 
            dimension: int = 1024,
            persist_directory: str = None
            ):
        """
        Args:
            embedding: 向量化服务
            dimension: 向量维度（text-embedding-v3 默认是1024
        """
        self._embedding = embedding
        self._dimension = dimension
        self._persist_directory = persist_directory

        # 尝试从磁盘加载，否则创建新的
        if persist_directory and self._load():
            print(f"从{persist_directory} 加载了已有知识库")
        else:
            # 创建 FAISS 索引（使用 L2 距离）
            self._index = faiss.IndexFlatL2(dimension)
            # 存储原始文档块（FAISS 只存向量，我们需要额外存储文本）
            self._chunks : list[DocumentChunk] = []

    def add_documents(self, chunks: list[DocumentChunk], knowledge_base_id: str = None) -> None:
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

        # 自动保存到本地磁盘
        self._save()

    def search(self, query, top_k = 3, knowledge_base_id: str = None):
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

    def clear(self, knowledge_base_id: str = None):
        """清空向量存储"""
        self._index = faiss.IndexFlatL2(self._dimension)
        self._chunks = []

        # 删除持久化文件
        if self._persist_directory:
            # 创建存储路径
            index_path = os.path.join(self._persist_directory, "index.faiss")
            chunks_path = os.path.join(self._persist_directory, "chunks.pkl")
            if os.path.exists(index_path):
                os.remove(index_path)
            if os.path.exists(chunks_path):
                os.remove(chunks_path)
            
    @property
    def count(self, knowledge_base_id: str = None) -> int:
        """返回存储的文档块数量"""
        return len(self._chunks)
    
    def _save(self) -> None:
        """保存到磁盘"""
        if not self._persist_directory:
            return
        
        os.makedirs(self._persist_directory, exist_ok=True)

        # 创建存储路径
        index_path = os.path.join(self._persist_directory, "index.faiss")
        chunks_path = os.path.join(self._persist_directory, "chunks.pkl")

        faiss.write_index(self._index, index_path)
        with open(chunks_path, "wb") as f:
            pickle.dump(self._chunks, f)
        
    def _load(self) -> bool:
        """从磁盘加载，成功返回 True"""
        if not self._persist_directory:
            return False
    
        # 创建存储路径
        index_path = os.path.join(self._persist_directory, "index.faiss")
        chunks_path = os.path.join(self._persist_directory, "chunks.pkl")

        if not os.path.exists(index_path) or not os.path.exists(chunks_path):
            return False
        
        try:
            self._index = faiss.read_index(index_path)
            with open(chunks_path, "rb") as f:
                self._chunks = pickle.load(f)
            return True
        except Exception as e:
            print(f"加载数据库失败:{e}")
            return False

