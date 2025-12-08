from functools import lru_cache

from ai_qa.config.settings import Settings
from ai_qa.infrastructure.llm.qwen_adapter import QwenAdapter
from ai_qa.infrastructure.memory.in_memory import InMemoryConversationMemory
from ai_qa.application.chat_service import ChatService
from ai_qa.domain.ports import LLMPort, ConversationMemoryPort

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

def get_chat_service() -> ChatService:
    """获取聊天服务"""
    return ChatService(
        llm=get_llm(),
        memory=get_memory()
    )