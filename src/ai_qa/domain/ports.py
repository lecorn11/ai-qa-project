from abc import ABC, abstractmethod
from .entities import Message, Conversation

class LLMPort(ABC):
    """LLM 服务端口（抽象接口）

    定义了与大模型模型交互的契约
    具体实现在 Infrastructure 层
    """

    @abstractmethod
    def chat(self,messages:list[Message],sys_prompt: str = None) -> str:
        """发送消息并获取回复

        Args:
            messages: 消息列表
            sys_prompt: 系统提示词(可选)
        Returns:
            AI 的回复内容
        """
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


