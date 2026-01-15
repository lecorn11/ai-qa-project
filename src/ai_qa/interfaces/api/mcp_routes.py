from fastapi import APIRouter, Depends

from ai_qa.application.mcp_settings_service import McpSettingsService
from ai_qa.infrastructure.database.models import User
from ai_qa.infrastructure.mcp.client import MCPClientService
from ai_qa.interfaces.api.dependencies import get_current_user, get_mcp_client, get_db, get_mcp_client

from sqlalchemy.orm import Session

from ai_qa.models.mcp import McpServerInfo, McpServersResponse, McpSettingsResponse, UpdateMcpSettingsRequest

router = APIRouter(prefix="/mcp", tags=["MCP 设置"])


def get_mcp_settings_service(
    db: Session = Depends(get_db),
    mcp_client: MCPClientService = Depends(get_mcp_client)
) -> McpSettingsService:
    """获取 MCP 设置服务"""
    return McpSettingsService(db, mcp_client)

@router.get(
    "/servers",
    response_model=McpServersResponse,
    summary="获取可用的 MCP Server 列表",
    responses={
        401:{"description": "未登录或 Token 无效"}
    }
)
async def get_available_servers(
    current_user: User = Depends(get_current_user),
    service: McpSettingsService = Depends(get_mcp_settings_service)
):
    """获取系统中配置的所有可用 MCP Server。
    
    返回的列表来自服务器配置文件 (mcp_servers.json)。
    """
    servers = service.get_available_servers()
    return McpServersResponse(
        servers=[McpServerInfo(**s) for s in servers]
    )

@router.get(
    "/settings",
    response_model=McpSettingsResponse,
    summary="获取当前用户的 MCP 设置",
    responses={
        401:{"description": "未登录或 Token 无效"}
    }
)
async def get_mcp_settings(
    current_user: User = Depends(get_current_user),
    service: McpSettingsService = Depends(get_mcp_settings_service)
):
    """
    获取当前用户的 MCP 设置，包括：
    - mcp_enabled: MCP 功能总开关
    - servers: 已启用的 MCP Server 列表
    """
    settings = service.get_user_settings(user_id=current_user.id)
    return McpSettingsResponse(**settings)

@router.put(
    "/settings",
    response_model=McpSettingsResponse,
    summary="更新 MCP 设置",
    responses={
        401:{"description": "未登录或 Token 无效"}
    }
)
async def update_mcp_settings(
    request: UpdateMcpSettingsRequest,
    current_user: User = Depends(get_current_user),
    service: McpSettingsService = Depends(get_mcp_settings_service)
):
    """
    更新当前用户的 MCP 设置（全量更新）。
    
    - mcp_enabled: 设置 MCP 总开关
    - servers: 要启用的 Server 名称列表，会替换现有设置
    
    无效的 Server 名称会被忽略。
    """
    settings = service.update_user_settings(
        user_id=current_user.id,
        mcp_enabled=request.mcp_enabled,
        servers=request.servers,
        )
    return McpSettingsResponse(**settings)