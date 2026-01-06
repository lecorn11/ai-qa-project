

from fastapi import APIRouter, Depends
from pydantic import BaseModel,Field

from ai_qa.application.agent_service import AgentService
from ai_qa.infrastructure.database.models import User
from ai_qa.interfaces.api.dependecnies import get_agent_service, get_current_user


router = APIRouter(prefix="/agent", tags=["Agent"])

class AgentChatRequest(BaseModel):
    """Agent 对话请求"""
    content: str = Field(..., description="用户信息", examples=["今天几号？帮我算一下 123 * 456"])
    session_id: str = Field(..., description="会话 ID")

class AgentChatResponse(BaseModel):
    """Agent 对话响应"""
    content: str = Field(..., description="AI 回复")
    session_id: str = Field(..., description="会话 ID")

@router.post(
    "/chat",
    response_model=AgentChatResponse,
    summary="Agent 对话",
    responses={
        401:{"description": "未登录或 Token 无效"}
    }
)
async def agent_chat(
    request: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    Agent 模式对话, AI 可自主调用工具，

    支持的工具：
    - **计算器**：数学计算
    - **时间**：获取当前日期时间
    - **知识库搜索**：检索知识库内容
    """

    response = agent_service.chat(
        session_id=request.session_id,
        user_input=request.content,
        user_id=current_user.id
    )

    return AgentChatResponse(
        content=response,
        session_id=request.session_id
    )
