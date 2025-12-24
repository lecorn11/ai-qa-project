from ai_qa.infrastructure.database import get_db
from ai_qa.infrastructure.vectorstore import PostgresVectorStore
from ai_qa.infrastructure.embedding.dashscope_embedding import DashScopeEmbeddingAdapter
from ai_qa.domain.entities import DocumentChunk
from ai_qa.config.settings import settings

# 获取数据库连接
db = next(get_db())

# 创建 Embedding
embedding = DashScopeEmbeddingAdapter(
    api_key=settings.llm_api_key,
    model_name=settings.embedding_model_name
)

# 创建向量存储
vector_store = PostgresVectorStore(db, embedding)

# 测试：统计数量
count = vector_store.count()
print(f"当前文档块数量: {count}")

db.close()
print("向量存储测试通过！")