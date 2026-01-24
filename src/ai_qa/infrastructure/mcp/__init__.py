# src/ai_qa/infrastructure/mcp/__init__.py
"""MCP (Model Context Protocol) 客户端模块

提供 MCP Server 连接管理和工具转换功能。
支持 stdio、SSE、Streamable HTTP 三种传输方式。
"""

from .client import (
    # 枚举
    TransportType,
    # 配置类
    MCPServerConfig,
    StdioServerConfig,
    SSEServerConfig,
    StreamableHTTPServerConfig,
    # 连接和服务
    MCPConnection,
    MCPClientService,
    # 预定义配置
    FILESYSTEM_SERVER,
)
from .config import load_mcp_config, get_server_names

__all__ = [
    # 枚举
    "TransportType",
    # 配置类
    "MCPServerConfig",
    "StdioServerConfig",
    "SSEServerConfig",
    "StreamableHTTPServerConfig",
    # 连接和服务
    "MCPConnection",
    "MCPClientService",
    # 配置加载
    "load_mcp_config",
    "get_server_names",
    # 预定义配置
    "FILESYSTEM_SERVER",
]