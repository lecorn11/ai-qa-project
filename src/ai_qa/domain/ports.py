from abc import ABC, abstractmethod
from typing import Generator
from .entities import DocumentChunk, Message, Conversation

class LLMPort(ABC):
    """LLM 服务端口（抽象接口）

    定义了与大模型模型交互的契约
    具体实现在 Infrastructure 层
    """

    @abstractmethod
    def chat(self,messages:list[Message],system_prompt: str = None) -> str:
        """发送消息并获取回复

        Args:
            messages: 消息列表
            system_prompt: 系统提示词(可选)
        Returns:
            AI 的回复内容
        """
        pass

    @abstractmethod
    def chat_stream(self, messages: list[Message], system_prompt: str = None) -> Generator[str, None, None]:
        """流式发送消息，逐步返回回复"""
        pass


class ConversationMemoryPort(ABC):
    """对话记忆存储端口(抽象接口)
    
    定义了对话历史存储的契约。
    具体实现可以是内存、Resis、数据库等。
    """

    @abstractmethod
    def get_conversation(self, session_id: str) -> Conversation:
        """获取对话，如果不存在则创建新的

        Args:
            session_id: 会话 ID

        Returns:
            对话实体
        """
        pass

    @abstractmethod
    def save_conversation(self, conversation: Conversation) -> None:
        """保存对话

        Args:
            conversation: 对话实体
        """
        pass

    @abstractmethod
    def clear_conversation(self, session_id: str) -> None:
        """清除指定会话的对话历史

        Args:
            session_id: 会话 ID
        """
        pass


class EmbeddingPort(ABC):
    """向量化服务端口"""

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """将文本列表转换为向量列表"""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """将查询文本转换为向量"""
        pass

class VectorStorePort(ABC):
    """向量存储端口"""

    @abstractmethod
    def add_documents(self, chunks: list[DocumentChunk]) -> None:
        """添加文档块到向量存储"""
        pass
    
    @abstractmethod
    def search(self, query: str, top_k: int = 3) -> list[DocumentChunk]:
        """搜索相关文档块"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空向量存储"""
        pass


