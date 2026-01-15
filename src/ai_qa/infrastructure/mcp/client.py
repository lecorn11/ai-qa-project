import asyncio
import logging

from dataclasses import dataclass, field
from typing import Any

from mcp import ClientSession, StdioServerParameters, stdio_client
from mcp.types import Tool as MCPTool
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, create_model

logger = logging.getLogger(__name__)

@dataclass
class MCPServerConfig:
    """MCP Server 配置"""
    name: str
    command: str
    args: list[str]
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None

@dataclass
class MCPConnection:
    """MCP 连接信息"""
    config: MCPServerConfig
    session: ClientSession
    tools: list[MCPTool]
    # 用于管理连接生命周期的上下文，保存、关闭时需要
    _stdio_context: Any = None
    _session_context: Any = None

@dataclass
class MCPClientService:
    """MCP 客户端服务"""

    def __init__(self, config_path: str = None):
        self._connections: dict[str, MCPConnection] = {}
        self._available_configs: dict[str, MCPServerConfig] = {}
        self._lock = asyncio.Lock()

        # 从配置文件加载可用配置
        if config_path:
            self._load_configs(config_path)

    def _load_configs(self, config_path: str):
        """从配置文件加载 MCP Server 配置"""
        from .config import load_mcp_config
        try:
            self._available_configs = load_mcp_config(config_path)
        except Exception as e:
            logger.error(f"加载 MCP 配置失败: {e}")

    def list_available_servers(self) -> list[str]:
        """列出所有可用（已配置）的 Server 名称"""
        return list(self._available_configs.keys())
    
    async def connect_by_name(self, names: list[str]) -> dict[str, list[MCPTool]]:
        """根据名称批量连接 MCP Server"""
        results = {}

        for name in names:
            # 跳过已连接
            if name in self._connections:
                logger.debug(f"Server '{name}' 已连接，使用现有连接")
                results[name] = self._connections[name].tools
                continue

            # 跳过不存在配置的情况
            if name not in self._available_configs:
                logger.warning(f"未找到 Server 配置: {name}, 可用配置: {list(self._available_configs.keys())}")
                continue

            # 连接
            try:
                tools = await self.connect(self._available_configs[name])
                results[name] = tools
            except Exception as e:
                logger.error(f"连接 Server '{name}' 失败: {e}")

        return results

    async def connect(self, config: MCPServerConfig) -> list[MCPTool]:
        """连接到 MCP Server
        
        Args:
            config: Server 配置
            
        Returns:
            该 Server 提供的工具列表
        """
        async with self._lock:
            # 如果已连接，先断开
            if config.name in self._connections:
                await self._disconnect_unsafe(config.name)
            
            logger.info(f"正在连接 MCP Server: {config.name}")
            logger.debug(f"命令：{config.command} {' '.join(config.args)}")

            try:
                # 构建连接参数
                server_params = StdioServerParameters(
                    command=config.command,
                    args=config.args,
                    env=config.env if config.env else None,
                    cwd=config.cwd,
                )

                # 建立连接
                stdio_context = stdio_client(server_params)
                read, write = await stdio_context.__aenter__()

                session_context = ClientSession(read, write)
                session = await session_context.__aenter__()

                # 初始化
                init_result = await session.initialize()
                server_info = init_result.serverInfo
                logger.info(f"已连接到{server_info.name} v{server_info.version}")

                # 获取工具列表
                tools_result = await session.list_tools()
                tools = tools_result.tools
                logger.info(f"发现{len(tools)} 个工具")

                # 保存连接
                self._connections[config.name] = MCPConnection(
                    config=config,
                    session=session,
                    tools=tools,
                    _stdio_context=stdio_context,
                    _session_context=session_context
                )

                return tools
            
            except Exception as e:
                logger.error(f"连接 MCPServer 失败：{config.name}, 错误: {e}")
                raise


    async def disconnect(self, server_name: str) -> bool:
        """断开与指定 Server 的连接"""
        async with self._lock:
            return await self._disconnect_unsafe(server_name)
    
    async def _disconnect_unsafe(self, server_name: str) -> bool:
        """断开连接（内部方法，不加锁）"""
        if server_name not in self._connections:
            return False
        
        conn = self._connections[server_name]
        logger.info(f"正在断开 MCP Server：{server_name}")

        try:
            # 关闭 session
            if conn._session_context:
                await conn._session_context.__aexit__(None, None, None)
            # 关闭 stdio
            if conn._stdio_context:
                await conn._stdio_context.__aexit__(None, None, None)
        except Exception as e:
            logger.warning(f"断开连接时出错: {e}")

        del self._connections[server_name]
        return True
    
    async def disconnect_all(self):
        """断开所有连接"""
        async with self._lock:
            for name in list(self._connections.keys()):
                await self._disconnect_unsafe(name)

    def list_connections(self) -> list[str]:
        """列出所有已连接的 Server"""
        return list(self._connections.keys())
    
    def list_tools(self, server_name: str = None) -> list[dict]:
        """列出工具
        
        Args:
            server_name: 指定 Server 名称，为 None 时列出所有
            
        Returns:
            工具信息列表
        """
        tools =[]

        connections = [self._connections[server_name]] if server_name else self._connections.values()

        for conn in connections:
            for tool in conn.tools:
                tools.append({
                    "server": conn.config.name,
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                })
        
        return tools
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: dict) -> Any:
        """调用 MCP 工具
        
        Args:
            server_name: Server 名称
            tool_name: 工具名称
            arguments: 工具参数
        
        Returns:
            工具执行结果
        """
        if server_name not in self._connections:
            raise ValueError(f"未连接到 Server: {server_name}")

        conn = self._connections[server_name]
        logger.info(f"调用工具: {server_name}/{tool_name} args={arguments}")

        try:
            result = await conn.session.call_tool(name=tool_name, arguments=arguments)
            logger.debug(f"工具返回：{result}")

            # 提取结果内容
            if result.content:
                # 通常返回 TextContent 列表
                contents = []
                for item in result.content:
                    if hasattr(item, "text"):
                        contents.append(item.text)
                    else:
                        contents.append(str(item))
                return "\n".join(contents)
            return str(result)
        
        except Exception as e:
            logger.error(f"工具调用失败: {e}")
            raise
    
    def get_langchain_tools(self, server_name: str = None) -> list[StructuredTool]:
        """将 MCP 工具转换为 LangChain StructuredTool
        
        Args:
            server_name: 指定 Server 名称， 为 None 时转换所有
            
        Returns:
            LangChain 工具列表
        """
        langchain_tools = []

        connections = [self._connections[server_name]] if server_name else self._connections.values()

        for conn in connections:
            for mcp_tool in conn.tools:
                lc_tool = self._convert_to_langchain_tool(conn.config.name, mcp_tool)
                langchain_tools.append(lc_tool)

        return langchain_tools

    def _convert_to_langchain_tool(self, server_name: str, mcp_tool: MCPTool) -> StructuredTool:
        """将单个 MCP 工具转换为 LangChain StructuredTool"""

        # 1. 从 JSON Schema 创建 Pydantic 模型作为 args_schema
        args_schema = self._create_args_schema(mcp_tool)

    # 2. 创建异步调用函数（改为 async）
        def make_tool_coro(srv_name: str, tool_name: str):
            async def tool_coro(**kwargs) -> str:
                """MCP 工具调用包装函数（异步）"""
                try:
                    return await self.call_tool(srv_name, tool_name, kwargs)
                except Exception as e:
                    return f"工具调用失败: {e}"
            return tool_coro
    
        # 2. 创建调用函数
        def make_tool_func(srv_name: str, tool_name: str):
            def tool_func(**kwargs) -> str:
                """MCP 工具调用包装函数"""
                try:
                    # 在新的事件循环中运行异步调用
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 如果已经在异步上下文中，创建 task
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(
                                asyncio.run, 
                                self.call_tool(srv_name, tool_name, kwargs)
                            )
                            return future.result()
                    else:
                        return asyncio.run(self.call_tool(srv_name, tool_name, kwargs))
                except Exception as e:
                    return f"工具调用失败: {e}"
            return tool_func
        
        # 3. 构建工具名称
        full_name = f"{server_name}__{mcp_tool.name}"

        # 4. 创建 StructuredTool
        return StructuredTool(
            name=full_name,
            description=f"[{server_name}] {mcp_tool.description}",
            args_schema=args_schema,
            # func=make_tool_func(server_name, mcp_tool.name),
            coroutine=make_tool_coro(server_name, mcp_tool.name),
        )

    def _create_args_schema(self, mcp_tool: MCPTool) -> type[BaseModel]:
        """从 MCP inputSchema 创建 Pydantic 模型"""

        input_schema = mcp_tool.inputSchema or {}
        properties = input_schema.get("properties",{})
        required = set(input_schema.get("required",[]))

        # 构建字段定义
        field_definitions = {}

        for prop_name, prop_info in properties.items():
            # 获取类型
            json_type = prop_info.get("type","string")
            python_type = self._json_type_to_python(json_type)

            # 获取描述
            description = prop_info.get("description","")

            # 是否必填
            if prop_name in required:
                field_definitions[prop_name] = (python_type, ...)
            else:
                field_definitions[prop_name] = (python_type | None, None)

        # 如果没有参数，创建空模型
        if not field_definitions:
            field_definitions["_placeholder"] = (str | None, None)

        # 动态创建 Pydantic 模型
        model_name = f"{mcp_tool.name.title().replace('_', '')}Args"
        return create_model(model_name, **field_definitions)

    def _json_type_to_python(self, json_type: str) -> type:
        """JSON Schema 类型转 Python 类型"""
        type_mapping = {
            "string": str,
            "number": float,
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        return type_mapping.get(json_type, str)
    

# ============ 预定义的 Server 配置 ============

# 官方 Filesystem Server
FILESYSTEM_SERVER = MCPServerConfig(
    name="filesystem",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
)

# 我们的知识库 Server（需要根据实际路径调整）
KNOWLEDGE_SERVER = MCPServerConfig(
    name="knowledge",
    command="/opt/homebrew/Caskroom/miniforge/base/envs/ai-qa/bin/python",
    args=["-m", "ai_qa.infrastructure.mcp.server"],
    cwd="/Users/lecorn/Projects/ai-qa-project",
    env={"PYTHONPATH": "/Users/lecorn/Projects/ai-qa-project/src"},
)







        
        

