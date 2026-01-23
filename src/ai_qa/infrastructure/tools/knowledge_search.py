import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

def create_knowledge_search_tool(knowledge_service, knowledge_base_id : str = None):
    """创建知识库搜索工具（工厂函数）
    
        Args:
        knowledge_service: KnowledgeService 实例
        knowledge_base_id: 知识库 ID
    """

    @tool
    def search_knowledge_base(query: str) -> str:
        """在知识库中搜索相关信息。
        
        当用户询问需要查询文档、资料、知识库内容的问题时，使用此工具。
        输入应该是一个清晰的搜索问题
        """
        logger.info("【本地】调用知识库搜索工具")
        # return knowledge_service.query(
        #     query
        # )

        try:
            # 调用知识库检索
            chunks = knowledge_service.get_relevant_chunks(query, top_k=1)

            if not chunks:
                return "知识库中没有找到相关内容"
            
            # 拼接检索结果
            results = []
            for i, chunk in enumerate(chunks, 1):
                results.append(f"{i} {chunk.content[:200]}")
            
            return "\n\n".join(results)
        except Exception as e:
            return f"搜索出错: {e}"
    
    return search_knowledge_base
