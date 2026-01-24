import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ai_qa.application.agent_service import AgentService
from ai_qa.application.chat_service import ChatService
from ai_qa.application.knowledge_service import KnowledgeService
from ai_qa.domain.entities import Conversation, MessageRole
from ai_qa.domain.exceptions import NotFoundException
from ai_qa.domain.ports import ConversationMemoryPort
from ai_qa.infrastructure.database.models import User
from ai_qa.infrastructure.mcp.client import MCPClientService
from ai_qa.interfaces.api.dependencies import (
    get_agent_service,
    get_chat_service,
    get_current_user,
    get_knowledge_service,
    get_mcp_client,
    get_memory,
)
from ai_qa.interfaces.api.schemas import (
    AgentChatRequest,
    AgentChatResponse,
    ConversationListResponse,
    ConversationResponse,
    MessageItem,
    MessageResponse,
    MessagesResponse,
    SendMessageRequest,
    SuccessResponse,
)

# 创建路由器
router = APIRouter(prefix="/conversations", tags=["对话"])


# ============ 会话管理 ============
@router.post(
    "",
    response_model=ConversationResponse,
    summary="创建会话",
    responses={401: {"description": "未登录或 Token 无效"}},
)
async def create_conversation(
    current_user: User = Depends(get_current_user),
    memory: ConversationMemoryPort = Depends(get_memory),
):
    """
    创建一个新的对话会话。

    创建后使用返回的 `session_id` 发送消息。
    """

    # 创建空对话
    conversation = Conversation(user_id=current_user.id)
    # 保存对话
    memory.save_conversation(conversation)

    return ConversationResponse(
        session_id=conversation.id,
        title=conversation.title or "新对话",
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.get(
    "",
    response_model=ConversationListResponse,
    summary="获取会话列表",
    responses={401: {"description": "未登录或 Token 无效"}},
)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    memory: ConversationMemoryPort = Depends(get_memory),
):
    """获取当前用户的所有对话"""

    conversations = memory.list_conversations(user_id=current_user.id)

    return ConversationListResponse(
        conversations=[
            ConversationResponse(
                session_id=conv.id,
                title=conv.title or "新对话",
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )
            for conv in conversations
        ]
    )


@router.delete(
    "/{session_id}",
    response_model=SuccessResponse,
    summary="删除会话",
    responses={
        401: {"description": "未登录或 Token 无效"},
        404: {"description": "会话不存在"},
    },
)
async def delete_conversation(
    session_id: str,
    current_user: User = Depends(get_current_user),
    memory: ConversationMemoryPort = Depends(get_memory),
):
    """删除指定的对话会话。"""

    success = memory.clear_conversation(session_id, user_id=current_user.id)

    if not success:
        raise NotFoundException("对话不存在")

    return SuccessResponse(message=f"会话 {session_id} 已删除。")


# ============ 消息：普通对话 ============
@router.get(
    "/{session_id}/messages",
    summary="获取消息历史",
    responses={
        401: {"description": "未登录或 Token 无效"},
        404: {"description": "会话不存在"},
    },
)
async def get_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    memory: ConversationMemoryPort = Depends(get_memory),
):
    """获取对话的消息历史"""

    conversation = memory.get_conversation(session_id, user_id=current_user.id)

    return MessagesResponse(
        session_id=session_id,
        messages=[
            MessageItem(
                role=msg.role.value, 
                content=msg.content,
                reasoning_steps=msg.reasoning_steps
            )
            for msg in conversation.messages
        ],
    )


@router.post(
    "/{session_id}/messages",
    response_model=MessageResponse,
    summary="发送消息",
    responses={
        401: {"description": "未登录或 Token 无效"},
        404: {"description": "会话不存在"},
    },
)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
    memory: ConversationMemoryPort = Depends(get_memory),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    """
    发送消息并获取 AI 回复。

    - **use_knowledge**: 设为 `true` 启用知识库问答
    - **knowledge_base_id**: 使用知识库时需指定知识库 ID
    """

    if (
        request.use_knowledge
        and knowledge_service.get_chunk_count(request.knowledge_base_id) > 0
    ):
        # 使用知识库回答
        response_content = knowledge_service.query(
            request.content, session_id=session_id
        )

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
        timestamp=last_message.timestamp,
    )


@router.post(
    "/{session_id}/messages/stream",
    summary="发送消息（流式）",
    responses={
        401: {"description": "未登录或 Token 无效"},
        404: {"description": "会话不存在"},
    },
)
async def send_message_stream(
    session_id: str,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
    memory: ConversationMemoryPort = Depends(get_memory),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    """
        发送消息并获取 AI 回复（流式响应）。

        使用 Server-Sent Events (SSE) 格式返回，实现打字机效果。

        响应格式：
    ```
        data: "你"
        data: "好"
        data: "！"
        data: [DONE]
    ```
    """
    # 流式暂时只支持普通对话，知识库对话后续可以扩展
    if (
        request.use_knowledge
        and knowledge_service.get_chunk_count(request.knowledge_base_id) > 0
    ):

        def generate():
            full_response = ""

            # 知识库模式用非流式返回
            for chunk in knowledge_service.query_stream(
                request.content,
                session_id=session_id,
                user_id=current_user.id,
                knowledge_base_id=request.knowledge_base_id,
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
        for chunk in chat_service.chat_stream(
            session_id, request.content, user_id=current_user.id
        ):
            # SSE 格式： data:{内容}\n\n
            yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ============ 消息：Agent 对话 ============
@router.post(
    "/{session_id}/messages/agent",
    response_model=AgentChatResponse,
    summary="Agent 对话",
    responses={
        401: {"description": "未登录或 Token 无效"},
        404: {"description": "会话不存在"},
    },
)
async def send_agent_message(
    session_id: str,
    request: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
    mcp_client: MCPClientService = Depends(get_mcp_client),
):
    """
    Agent 模式对话, AI 可自主调用工具，

    支持的工具：
    - **计算器**：数学计算
    - **时间**：获取当前日期时间
    - **知识库搜索**：检索知识库内容
    """

    if request.mcp_servers:
        await mcp_client.connect_by_name(request.mcp_servers)
        mcp_tools = mcp_client.get_langchain_tools()
    else:
        mcp_tools = []

    response = await agent_service.chat(
        session_id=session_id,
        user_input=request.content,
        user_id=current_user.id,
        extra_tools=mcp_tools,
    )

    return AgentChatResponse(content=response, session_id=session_id)


@router.post(
    "/{session_id}/messages/agent/stream",
    summary="Agent 对话（流式）",
    responses={
        200: {"description": "SSE 流式响应", "content": {"text/event-stream": {}}},
        401: {"description": "未登录或 Token 无效"},
        404: {"description": "会话不存在"},
    },
)
async def send_agent_message_stream(
    session_id: str,
    request: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
    mcp_client: MCPClientService = Depends(get_mcp_client),
):
    """
    Agent 模式对话（流式）, AI 可自主调用工具，

    支持的工具：
    - **计算器**：数学计算
    - **时间**：获取当前日期时间
    - **知识库搜索**：检索知识库内容

    返回 SSE 事件流：
    - `tool_start`: 开始调用工具
    - `tool_result`: 工具返回结果
    - `answer`: 最终回答（逐字）
    - `done`: 完成
    """

    if request.mcp_servers:
        await mcp_client.connect_by_name(request.mcp_servers)
        mcp_tools = mcp_client.get_langchain_tools()
    else:
        mcp_tools = []

    return StreamingResponse(
        agent_service.chat_stream(
            session_id=session_id,
            user_input=request.content,
            user_id=current_user.id,
            extra_tools=mcp_tools,
        ),
        media_type="text/event-stream",
    )
