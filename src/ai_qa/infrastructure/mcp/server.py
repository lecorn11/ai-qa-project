"""MCP server - 知识库服务"""
import logging
from mcp.server.fastmcp import FastMCP

from ai_qa.application.knowledge_base_service import KnowledgeBaseService
from ai_qa.application.knowledge_service import KnowledgeService
from ai_qa.config.settings import settings
from ai_qa.infrastructure.database.connection import SessionLocal
from ai_qa.infrastructure.embedding.dashscope_embedding import DashScopeEmbeddingAdapter
from ai_qa.infrastructure.vectorstore.postgres_store import PostgresVectorStore

# ============ 创建依赖 ============
logger = logging.getLogger(__name__)
# 数据库会话
db = SessionLocal()

# Embedding 服务
embedding = DashScopeEmbeddingAdapter(
    api_key=settings.llm_api_key.get_secret_value(),
    model_name=settings.embedding_model_name
)

# 向量存储
vector_store = PostgresVectorStore(db, embedding)

# 知识库服务
knowledge_service = KnowledgeService(
    vector_store=vector_store,
    llm=None,
    memory=None,
    db=db
)

# 知识库管理服务
kb_service = KnowledgeBaseService(db)


# ============ 创建 MCP Server ============

mcp = FastMCP("AI-QA Knowledge Base")

@mcp.tool()
def search_knowledge(query: str, kb_id: str = None, top_k: int = 3) -> str:
    """
    search_knowledge 的 Docstring
    
    :param query: 说明
    :type query: str
    :param kb_id: 说明
    :type kb_id: str
    :param top_k: 说明
    :type top_k: int
    :return: 说明
    :rtype: str
    """
    logger.info("【MCP】调用知识库搜索工具")

    chunks = vector_store.search(query, knowledge_base_id=kb_id, top_k=top_k)

    if not chunks:
        return "未找到相关内容"
    
    results = []
    for i, chunk in enumerate(chunks, 1):
        results.append(f"【{i}】{chunk.content}")
    
    return "\n\n".join(results)

@mcp.resource("knowledge://bases")
def list_knowledge_bases() -> str:
    """获取所有知识库列表
    
    返回 JSON 格式的知识库信息，包括 ID、名称、描述"""
    
    from ai_qa.infrastructure.database.models import KnowledgeBase as KBModel

    kbs = db.query(KBModel).filter(KBModel.status == 1).all()

    result = [
        {
            "id": kb.id,
            "name": kb.name,
            "description": kb.description
        }
        for kb in kbs
    ]

    import json
    return json.dumps(result, ensure_ascii=False, indent=2)


# ============ 启动入口 ============

if __name__ == "__main__":
    mcp.run()