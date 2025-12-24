from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import json

from ai_qa.domain.entities import MessageRole, Conversation
from ai_qa.application.knowledge_service import KnowledgeService
from ai_qa.config.settings import settings
from ai_qa.infrastructure.database.models import User
from ai_qa.infrastructure.llm.qwen_adapter import QwenAdapter
from ai_qa.infrastructure.memory.in_memory import InMemoryConversationMemory
from ai_qa.application.chat_service import ChatService
from ai_qa.domain.ports import ConversationMemoryPort
from ai_qa.interfaces.api.dependecnies import (
    get_chat_service, 
    get_knowledge_service,
    get_memory,
    get_current_user, 
    get_current_user_optional
)
from ai_qa.models.schemas import (
    SendMessageRequest,
    MessageResponse,
    ConversationResponse,
    ConversationListResponse,
    SuccessResponse,
)

# 创建路由器
router = APIRouter(prefix="/conversations", tags=["对话"])

@router.post("", response_model=ConversationResponse)
async def create_conversation(
    current_user: User = Depends(get_current_user),
    memory: ConversationMemoryPort = Depends(get_memory)
):
    """创建新对话"""
    
    # 创建空对话
    conversation = Conversation(session_id="0")
    conversation.user_id = current_user.id

    # 保存对话
    memory.save_conversation(conversation)

    return ConversationResponse(
        sessiong_id=conversation.session_id,
        title=conversation.title or "新对话",
        created_at=conversation.created_at,
        update_at = conversation.updated_at
    )

@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    memory: ConversationMemoryPort = Depends(get_memory)
):
    """获取当前用户的所有对话"""

    conversations = memory.list_conversations(user_id=current_user.id)

    return ConversationListResponse(
        conversations=[
            ConversationResponse(
                sessiong_id=conv.session_id,
                title=conv.title or "新对话",
                created_at=conv.created_at,
                update_at = conv.updated_at
            )
            for conv in conversations
        ]
    )

@router.post("/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
    memory: ConversationMemoryPort = Depends(get_memory),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """发送消息并获取 AI 回复（支持知识库）"""

    if request.use_knowledge and knowledge_service.chunk_count > 0:
        # 使用知识库回答
        response_content = knowledge_service.query(request.conten,session_id=session_id)

        # 同时保存到对话历史
        conversation = memory.get_conversation(session_id, current_user.id)

        conversation.add_message(MessageRole.USER, request.content)
        conversation.add_message(MessageRole.ASSISTANT, response_content)
        memory.save_conversation(conversation)
        
        last_message = conversation.messages[-1]
    else:
        response_content = chat_service.chat(session_id, request.content)
        # 获取刚添加的 AI 消息
        conversation = memory.get_conversation(session_id, current_user.id)
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
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
    memory: ConversationMemoryPort = Depends(get_memory),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """发送消息并获取 AI 回复（流式）"""
    # 流式暂时只支持普通对话，知识库对话后续可以扩展
    if request.use_knowledge and knowledge_service.chunk_count > 0:

        def generate():
            full_response = ""

            # 知识库模式用非流式返回
            for chunk in knowledge_service.query_stream(
                request.content,
                session_id=session_id,
                user_id=current_user.id
            ):
                full_response += chunk
                yield f"data: {json.dumps(chunk)}\n\n"

            # 同时保存到对话历史
            conversation = memory.get_conversation(session_id, user_id=current_user.id)
            conversation.add_message(MessageRole.USER, request.content)
            conversation.add_message(MessageRole.ASSISTANT, full_response)
            memory.save_conversation(conversation)

            yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
 
    def generate():
        for chunk in chat_service.chat_stream(session_id,request.content,user_id=current_user.id):
            # SSE 格式： data:{内容}\n\n
            yield f"data: {json.dumps(chunk)}\n\n" 
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )

@router.get("/{session_id}/messages")
async def get_conversation(
    session_id: str,
    current_user: User = Depends(get_current_user),
    memory: ConversationMemoryPort = Depends(get_memory)
):
    """获取对话的消息历史"""

    conversation = memory.get_conversation(session_id, user_id=current_user.id)

    return {
        "session_id": session_id,
        "messages": [
            {"role": msg.role.value, "content": msg.content}
            for msg in conversation.messages
        ]
    }

@router.delete("/conversations/{session_id}", response_model=SuccessResponse)
async def delete_conversation(
    session_id: str,
    current_user: User = Depends(get_current_user),
    memory: ConversationMemoryPort = Depends(get_memory),
):
    """删除会话"""

    success = memory.clear_conversation(session_id, user_id=current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="对话不存在")

    return SuccessResponse(messaage=f"会话 {session_id} 已删除。")



