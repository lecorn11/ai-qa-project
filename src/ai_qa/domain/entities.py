from dataclasses import dataclass, field
from enum import Enum
from turtle import update
from typing import Optional
from datetime import datetime

from ai_qa.infrastructure import document

class MessageRole(Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

@dataclass
class Message:
    """消息实体"""
    role: MessageRole
    content: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> dict:
        """转换为字典格式（用于 API 调用）"""
        return {
            "role": self.role.value,
            "content": self.content
        }

@dataclass
class Conversation:
    """对话实体"""
    session_id: str
    messages: list[Message] = field(default_factory=list)
    user_id: Optional[int] = None
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.messages is None:
            self.messages = []
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def add_message(self, role: MessageRole, content: str) -> Message:
        """添加消息到对话"""
        message = Message(role=role, content=content)
        self.messages.append(message)
        return message

    def get_messages_as_dicts(self) -> list[dict]:
        """获取所有消息的字典格式"""
        return [msg.to_dict() for msg in self.messages]

@dataclass
class DocumentChunk:
    """文档实体块"""
    content: str
    metadata: dict = field(default_factory=dict)
    embedding: Optional[list[float]] = None
    document_id: Optional[int] = None
    chunk_id: str = None


    def __post_init__(self):
        if self.chunk_id is None:
            self.chunk_id = f"chunk_{hash(self.content)}"

@dataclass
class KnowledgeBase:
    """知识库实体"""
    name: str
    description: str = ""
    documnet_count: int = 0
    create_at: datetime = None

    def __post_init__(self):
        if self.create_at is None:
            self.create_at = datetime.now()