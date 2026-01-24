from datetime import datetime
from sqlalchemy.orm import Session

from ai_qa.domain.entities import Conversation, Message, MessageRole
from ai_qa.domain.exceptions import ValidationException
from ai_qa.domain.ports import ConversationMemoryPort
from ai_qa.infrastructure.database.models import (
    Conversation as ConversationModel,
    Message as MessageModel
)


class PostgresConversationMemory(ConversationMemoryPort):
    """基于 PostgreSQL 的对话记忆"""

    def __init__(self, db: Session):
        self._db = db
    
        
    def get_conversation(self, session_id: str, user_id: str = None) -> Conversation:
        """获取对话"""
        # 参数校验（Guard Clause 卫语句）
        if not session_id:
            raise ValidationException("session_id 不能为空")
        
        # 构建查询条件
        contitions = [ConversationModel.id == session_id]
        if user_id:
            contitions.append(ConversationModel.user_id == user_id)
        
        # 查询会话数据模型
        db_conversation = self._db.query(ConversationModel).filter(*contitions).first()

        # 不存在则返回空会话实体
        if not db_conversation:
            return Conversation(id=session_id, user_id=user_id)

        # 查询消息数据模型
        db_messages = self._db.query(MessageModel).filter(
            MessageModel.conversation_id == db_conversation.id
        ).order_by(
            MessageModel.created_at
        ).all()

        # 消息数据模型 -> 消息领域实体
        messages = [
            Message(
                role=MessageRole.USER if msg.role == "user" else MessageRole.ASSISTANT,
                content=msg.content,
                reasoning_steps=msg.reasoning_steps, # 新增推理步骤字段
            )
            for msg in db_messages
        ]
        
        # 创建并返回 会话领域实体
        return Conversation(
            id=db_conversation.id,
            user_id=db_conversation.user_id,
            messages=messages,
            created_at=db_conversation.created_at,
            updated_at=db_conversation.updated_at
        )

    def save_conversation(self, conversation: Conversation) -> None:
        """保存对话"""
        # 查询数据库中是否存在该会话
        db_conversation = None
        if conversation.id:
            db_conversation = self._db.query(ConversationModel).filter(
                ConversationModel.id == conversation.id
            ).first()

        if not db_conversation:
            # 创建新对话
            db_conversation = ConversationModel(
                user_id = conversation.user_id,
                title = self._generate_title(conversation),
                status = 1, # 默认状态-启用,
                created_at = conversation.created_at
            )
            self._db.add(db_conversation)
            self._db.flush()  # 写入数据库（没有提交事务）获取自增 ID
            conversation.id = str(db_conversation.id) # 确保返回字符串类型
        
        # 更新时间
        db_conversation.updated_at = datetime.now()
        
        # 获取已有消息数量
        existing_count = self._db.query(MessageModel).filter(
            MessageModel.conversation_id == db_conversation.id
        ).count()

        # 只保存新消息
        new_messages = conversation.messages[existing_count:]
        for msg in new_messages:
            db_message = MessageModel(
                conversation_id = db_conversation.id,
                role = msg.role.value,
                content = msg.content,
                reasoning_steps = msg.reasoning_steps,  # 保存推理步骤
            )
            self._db.add(db_message)

        self._db.commit()
    
    def list_conversations(self, user_id: str) -> list[Conversation]:
        """列出用户的所有会话"""
        db_conversations = self._db.query(ConversationModel).filter(
            ConversationModel.user_id == user_id,
            ConversationModel.status == 1  # 仅启用状态
        ).order_by(ConversationModel.updated_at.desc()).all()

        conversations = [
            Conversation(
                id=str(db_conv.id),
                user_id=db_conv.user_id,
                title=db_conv.title,
                created_at=db_conv.created_at,
                updated_at=db_conv.updated_at
            )
            for db_conv in db_conversations
        ]

        return conversations
        
    def clear_conversation(self, session_id: str, user_id: str = None) -> bool:
        """删除对话（软删除）"""
        # 查询数据库中是否存在该会话
        query = self._db.query(ConversationModel).filter(
            ConversationModel.id == session_id
        )
        if user_id:
            query = query.filter(ConversationModel.user_id == user_id)
        db_conversation = query.first()
        if not db_conversation:
            return False
        
        # 软删除-更新状态
        db_conversation.status = -1  # 软删除-标记为已删除
        self._db.commit()
        return True

    def _generate_title(self, conversation: Conversation) -> str:
        """从第一条消息生成标题"""
        if conversation.messages:
            first_msg = conversation.messages[0].content
            return first_msg[:50] + "..." if len(first_msg) > 50 else first_msg
        return "新对话"
