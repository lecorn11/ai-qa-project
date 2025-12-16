from functools import lru_cache

from ai_qa.application.knowledge_service import KnowledgeService
from ai_qa.config import settings
from ai_qa.config.settings import Settings
from ai_qa.infrastructure.embedding.dashscope_embedding import DashScopeEmbeddingAdapter
from ai_qa.infrastructure.llm.qwen_adapter import QwenAdapter
from ai_qa.infrastructure.memory.in_memory import InMemoryConversationMemory
from ai_qa.application.chat_service import ChatService
from ai_qa.domain.ports import EmbeddingPort, LLMPort, ConversationMemoryPort, VectorStorePort
from ai_qa.infrastructure.vectorstore.faiss_store import FaissVectorStore
from ai_qa.interfaces import api

@lru_cache
def get_settings() -> Settings:
    """获取配置（缓存，只创建一次）"""
    return Settings()

@lru_cache
def get_llm() -> LLMPort:
    """获取 LLM 实例（单例）"""
    settings = get_settings()
    return QwenAdapter(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model_name=settings.llm_model
    )

@lru_cache
def get_memory() -> ConversationMemoryPort:
    """获取记忆存储实例（单例）"""
    return InMemoryConversationMemory()

@lru_cache
def get_embedding() -> EmbeddingPort:
    """获取 Embedding 实例（单例）"""
    settings = get_settings()
    return DashScopeEmbeddingAdapter(
        model_name=settings.embedding_model_name,
        api_key=settings.llm_api_key
    )

@lru_cache
def get_vector_store() -> VectorStorePort:
    """获取向量存储实例（单例）"""
    embedding = get_embedding()
    settings = get_settings()
    return FaissVectorStore(
        embedding = embedding,
        persist_directory=settings.knowledge_persist_dir
    )

def get_chat_service() -> ChatService:
    """获取聊天服务"""
    return ChatService(
        llm=get_llm(),
        memory=get_memory()
    )

@lru_cache
def get_knowledge_service() -> KnowledgeService:
    """获取知识库服务（单例）"""
    return KnowledgeService(
        vector_store=get_vector_store(),
        llm=get_llm()
    )