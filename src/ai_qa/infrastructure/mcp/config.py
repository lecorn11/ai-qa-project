
import json
import logging
from pathlib import Path

from ai_qa.infrastructure.mcp.client import MCPServerConfig

logger = logging.getLogger(__name__)


def load_mcp_config(config_path: str | Path) -> dict[str, MCPServerConfig]:
    """加载 MCP 服务器配置文件

    Args:
        config_path: 配置文件路径
        
    Returns:
        服务器名称 -> MCPServerConfig 的映射字典
        
    Raises:
        FileNotFoundError: 配置文件不存在
        json.JSONDecodeError: JSON 格式错误
        ValueError: 配置格式不符合预期
    """
    path = Path(config_path)

    if not path.exists():
        logger.warning(f"MCP 配置文件不存在: {path}")
        return {}
    
    logger.info(f"加载 MCP 配置: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw_config = json.load(f)

    # 验证根结构
    if "mcpServers" not in raw_config:
        raise ValueError("配置文件缺少 'mcpServers' 字段")
    
    servers = raw_config["mcpServers"]
    if not isinstance(servers, dict):
        raise ValueError("'mcpServers' 必须是对象类型")

    # 转换为 MCPServerConfig
    configs = {}
    for name, server_config in servers.items():
        try:
            config = _parse_server_config(name, server_config)
            configs[name] = config
            logger.debug(f"已加载 MCP Server 配置: {name}")
        except Exception as e:
            logger.error(f"解析 MCP Server '{name}' 配置错误:{e}")
            raise ValueError((f"Server '{name}' 配置错误:{e}"))
    
    logger.info(f"共加载 {len(configs)} 个 MCP Server 配置")
    return configs

def _parse_server_config(name: str, config: dict) -> MCPServerConfig:
    """解析单个服务器配置
    Args:
        name: 服务器名称
        config: 原始配置字典
        
    Returns:
        MCPServerConfig 对象
    """

    # 必填字段
    if "command" not in config:
        raise ValueError("缺少必填字段 'command'")
    
    return MCPServerConfig(
        name=name,
        command=config["command"],
        args=config.get("args",[]),
        env=config.get("env",{}),
        cwd=config.get("cwd"),
    )

def get_server_names(config_path: str | Path) -> list[str]:
    """获取配置文件中所有可用的服务器名称
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        服务器名称列表
    """
    configs=load_mcp_config(config_path)
    return list(configs.keys())