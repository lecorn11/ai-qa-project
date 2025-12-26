from ai_qa.domain.ports import ConversationMemoryPort
from ai_qa.domain.entities import Conversation

class InMemoryConversationMemory(ConversationMemoryPort):
    """内存存储实现
    
    将对话历史存储在内存中（程序重启后丢失）
    未来可以替换为 Redis、数据库等持久化实现
    """

    def __init__(self):
        self._store: dict[str, Conversation] = {}
    
    def get_conversation(self, session_id: str, user_id: str = None) -> Conversation:
        """获取对话，不存在则创建"""
        if session_id not in self._store:
            conversation = Conversation(id=session_id)
            conversation.user_id = user_id
            self._store[session_id] = conversation
        return self._store[session_id]
        
    def save_conversation(self, conversation: Conversation) -> None:
        """保存对话"""
        self._store[conversation.id] = conversation

    def list_conversations(self, user_id: str) -> list[Conversation]:
        return list(self._store.values())

    def clear_conversation(self, session_id: str) -> bool:
        """清除对话"""
        if session_id in self._store:
            del self._store[session_id]
            return True
        return False
                


        