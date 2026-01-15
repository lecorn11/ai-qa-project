from datetime import datetime
from pydantic import BaseModel, Field

class McpServerInfo(BaseModel):
    """MCP Server 信息"""
    name: str = Field(..., description="Server 名称（配置文件中的 key）")
    description: str | None = Field(None, description="Server 描述")

class McpServersResponse(BaseModel):
    """可用的 MCP Server 列表响应"""
    servers: list[McpServerInfo] = Field(..., description="可用的 Server 列表")

class McpSettingsResponse(BaseModel):
    """用户 MCP 设置响应"""
    mcp_enabled: bool = Field(..., description="MCP 总开关")
    servers: list[str] = Field(..., description="已启用的 Server 名称列表")

class UpdateMcpSettingsRequest(BaseModel):
    """更新 MCP 设置请求"""
    mcp_enabled: bool = Field(..., description="MCP 总开关")
    servers: list[str] = Field(default_factory=list, description="要启用的 Server 名称列表")

