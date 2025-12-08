from fastapi import APIRouter, HTTPException

from ai_qa.config.settings import settings
from ai_qa.infrastructure.llm.qwen_adapter import QwenAdapter
from ai_qa.infrastructure.memory.in_memory import InMemoryConversationMemory
from ai_qa.application.chat_service import ChatService
from ai_qa.models.schemas import (
    SendMessageRequest,
    MessageResponse,
    ConversationResponse,
    ConversationListResponse,
    ConversationListItem,
    SuccessResponse,
)

# 创建路由器
router = APIRouter()

# 创建服务实例（依赖注入，后续优化）
llm = QwenAdapter(
    api_key = settings.llm_api_key,
    base_url = settings.llm_base_url,
    model_name = settings.llm_model
)
memory = InMemoryConversationMemory()
chat_service = ChatService(
    llm = llm,
    memory = memory
)

@router.post("/conversations/{session_id}/messages", response_model=MessageResponse)
async def send_message(session_id: str, request: SendMessageRequest):
    """发送消息并获取 AI 回复"""

    response_content = chat_service.chat(session_id, request.content)

    # 获取刚添加的 AI 消息
    conversation = memory.get_conversation(session_id)
    last_message = conversation.messages[-1]

    return MessageResponse(
        role=last_message.role.value,
        content=last_message.content,
        timestamp=last_message.timestamp
    )

@router.get("/conversations/{session_id}", response_model=ConversationResponse)
async def get_conversation(session_id: str):
    """获取会话的所有消息"""

    conversation = memory.get_conversation(session_id)

    messages = [
        MessageResponse(
            role=msg.role.value,
            content=msg.content,
            timestamp=msg.timestamp)
        for msg in conversation.messages
    ]

    return ConversationResponse(
        sessiong_id=session_id,
        messages=messages,
        created_at=conversation.created_at
    )

@router.delete("/conversations/{session_id}", response_model=SuccessResponse)
async def delete_conversation(session_id: str):
    """删除会话"""

    chat_service.clear_conversation(session_id)

    return SuccessResponse(messaage=f"会话 {session_id} 已删除。")

@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations():
    """获取所有会话列表"""
    
    conversations = [
        ConversationListItem(
            session_id=conv.session_id,
            create_at=conv.created_at,
            message_count=len(conv.messages)
        )
        for conv in memory._store.values()
    ]

    return ConversationListResponse(conversations=conversations)

