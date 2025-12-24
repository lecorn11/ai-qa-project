from functools import lru_cache
from operator import ge
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ai_qa.application.knowledge_service import KnowledgeService
from ai_qa.application.user_service import UserService
from ai_qa.config.settings import Settings
from ai_qa.infrastructure.auth.security import verify_token
from ai_qa.infrastructure.database.connection import get_db
from ai_qa.infrastructure.database.models import User
from ai_qa.infrastructure.embedding.dashscope_embedding import DashScopeEmbeddingAdapter
from ai_qa.infrastructure.llm.qwen_adapter import QwenAdapter
from ai_qa.infrastructure.memory.in_memory import InMemoryConversationMemory
from ai_qa.application.chat_service import ChatService
from ai_qa.domain.ports import EmbeddingPort, LLMPort, ConversationMemoryPort, VectorStorePort
from ai_qa.infrastructure.memory.postgres_memory import PostgresConversationMemory
from ai_qa.infrastructure.vectorstore.faiss_store import FaissVectorStore
from ai_qa.infrastructure.vectorstore.postgres_store import PostgresVectorStore

# ============ 配置 ============

@lru_cache
def get_settings() -> Settings:
    """获取配置（缓存，只创建一次）"""
    return Settings()

# ============ AI 相关（单例）============
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
def get_embedding() -> EmbeddingPort:
    """获取 Embedding 实例（单例）"""
    settings = get_settings()
    return DashScopeEmbeddingAdapter(
        model_name=settings.embedding_model_name,
        api_key=settings.llm_api_key
    )

# ============ 数据库相关（每次请求）============

def get_memory(db: Session = Depends(get_db)) -> ConversationMemoryPort:
    """获取记忆存储实例"""
    # return InMemoryConversationMemory()
    return PostgresConversationMemory(db)

def get_vector_store(db: Session = Depends(get_db)) -> VectorStorePort:
    """获取向量存储实例"""
    # embedding = get_embedding()
    # settings = get_settings()
    # return FaissVectorStore(
    #     embedding = embedding,
    #     persist_directory=settings.knowledge_persist_dir
    # )
    return PostgresVectorStore(db, get_embedding())

# ============ 服务层（每次请求）============

def get_chat_service(
    memory: ConversationMemoryPort = Depends(get_memory)
) -> ChatService:
    """获取聊天服务"""
    return ChatService(
        llm=get_llm(),
        memory=memory
    )

@lru_cache
def get_knowledge_service(
    vector_store: VectorStorePort = Depends(get_vector_store),
    memory: ConversationMemoryPort = Depends(get_memory)
) -> KnowledgeService:
    """获取知识库服务"""
    return KnowledgeService(
        vector_store=vector_store,
        llm=get_llm(),
        memory=memory
    )

# ====== 用户认证 ======

security = HTTPBearer(auto_error=False)

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """获取用户服务"""
    return UserService(db)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前登录用户（必须登录）"""
    if not credentials:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "未提供认证信息",
        )
    
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Token 无效或已过期",
        )
    
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "用户不存在",
        )
    
    if user.status != 1:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "用户账号已被禁用",
        )
    
    return user

def get_current_user_optional(
    creaentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User | None:
    """获取当前用户（可选，未登录返回 None）"""
    if not creaentials:
        return None
    
    payload = verify_token(creaentials.credentials)
    if not payload:
        return None
    
    user_id = payload.get("user_id")
    return db.query(User).filter(User.id == user_id).first()