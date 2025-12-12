from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from ai_qa.application.knowledge_service import KnowledgeService
from ai_qa.config.settings import settings
from ai_qa.infrastructure.llm.qwen_adapter import QwenAdapter
from ai_qa.infrastructure.memory.in_memory import InMemoryConversationMemory
from ai_qa.application.chat_service import ChatService
from ai_qa.domain.ports import ConversationMemoryPort
from ai_qa.interfaces.api.dependecnies import get_chat_service, get_knowledge_service,get_memory
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

@router.post("/conversations/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    chat_service: ChatService = Depends(get_chat_service),
    memory: ConversationMemoryPort = Depends(get_memory),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """发送消息并获取 AI 回复（支持知识库）"""

    if request.use_knowledge and knowledge_service.chunk_count > 0:
        # 使用知识库回答
        response_content = knowledge_service.query(request.content)

        # 同时保存到对话历史
        conversation = memory.get_conversation(session_id)
        from ai_qa.domain.entities import MessageRole
        conversation.add_message(MessageRole.USER, request.content)
        conversation.add_message(MessageRole.ASSISTANT, response_content)
        memory.save_conversation(conversation)
        
        last_message = conversation.messages[-1]
    else:
        response_content = chat_service.chat(session_id, request.content)
        # 获取刚添加的 AI 消息
        conversation = memory.get_conversation(session_id)
        last_message = conversation.messages[-1]

    return MessageResponse(
        role=last_message.role.value,
        content=last_message.content,
        timestamp=last_message.timestamp
    )

@router.post("/conversations/{session_id}/messages/stream")
async def send_message_stream(
    session_id: str,
    request: SendMessageRequest,
    chat_service: ChatService = Depends(get_chat_service),
    memory: ConversationMemoryPort = Depends(get_memory),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """发送消息并获取 AI 回复（流式）"""
    # 流式暂时只支持普通对话，知识库对话后续可以扩展
    if request.use_knowledge:
        # 知识库模式用非流式返回
        response_content = knowledge_service.query(request.content)
        
        def generate():
            yield f"data: {response_content}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
 
    def generate():
        for chunk in chat_service.chat_stream(session_id,request.content):
            # SSE 格式： data:{内容}\n\n
            yield f"data: {chunk}\n\n" 
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )

@router.get("/conversations/{session_id}", response_model=ConversationResponse)
async def get_conversation(
    session_id: str,
    memory: ConversationMemoryPort = Depends(get_memory)
):
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
async def delete_conversation(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service),
):
    """删除会话"""

    chat_service.clear_conversation(session_id)

    return SuccessResponse(messaage=f"会话 {session_id} 已删除。")

@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    memory: ConversationMemoryPort = Depends(get_memory)
):
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

