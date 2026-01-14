"""
MCPClientService 测试脚本

测试目标：
1. 连接到 MCP Server
2. 获取工具列表
3. 转换为 LangChain 工具
4. 调用工具
"""

import asyncio
import sys
sys.path.insert(0, "src")

from ai_qa.infrastructure.mcp.client import (
    MCPClientService,
    MCPServerConfig,
    FILESYSTEM_SERVER,
)


async def test_mcp_client_service():
    """测试 MCPClientService"""
    
    print("=" * 60)
    print("测试 MCPClientService")
    print("=" * 60)
    
    # 1. 创建服务实例
    client = MCPClientService()
    
    try:
        # 2. 连接到 Filesystem Server
        print("\n[1] 连接到 Filesystem Server...")
        tools = await client.connect(FILESYSTEM_SERVER)
        print(f"    ✅ 连接成功，发现 {len(tools)} 个工具")
        
        # 3. 列出所有连接
        print("\n[2] 已连接的 Server:")
        for name in client.list_connections():
            print(f"    - {name}")
        
        # 4. 列出工具详情
        print("\n[3] 工具列表:")
        for tool_info in client.list_tools():
            print(f"    📌 {tool_info['server']}/{tool_info['name']}")
            print(f"       {tool_info['description'][:50]}...")
        
        # 5. 直接调用工具
        print("\n[4] 测试直接调用工具 (call_tool)...")
        result = await client.call_tool(
            server_name="filesystem",
            tool_name="read_file",
            arguments={"path": "/private/tmp/test.txt"}
        )
        print(f"    ✅ read_file 结果: {result[:100]}...")
        
        # 6. 转换为 LangChain 工具
        print("\n[5] 转换为 LangChain 工具...")
        lc_tools = client.get_langchain_tools()
        print(f"    ✅ 转换了 {len(lc_tools)} 个工具")
        
        for tool in lc_tools[:3]:  # 只显示前3个
            print(f"\n    📌 {tool.name}")
            print(f"       描述: {tool.description[:60]}...")
            print(f"       参数: {tool.args_schema.model_fields.keys()}")
        
        # 7. 通过 LangChain 工具调用
        print("\n[6] 测试 LangChain 工具调用...")
        read_file_tool = next(
            (t for t in lc_tools if "filesystem__read_file" in t.name), None
        )
        if read_file_tool:
            result = await read_file_tool.ainvoke({"path": "/private/tmp/test.txt"})
            print(f"    ✅ LangChain 调用结果: {result[:100]}...")
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 8. 断开所有连接
        print("\n[清理] 断开所有连接...")
        await client.disconnect_all()
        print("    ✅ 已断开")


async def test_multiple_servers():
    """测试连接多个 Server"""
    
    print("\n" + "=" * 60)
    print("测试连接多个 MCP Server")
    print("=" * 60)
    
    client = MCPClientService()
    
    # 定义多个 Server（这里用两个不同路径的 filesystem 模拟）
    servers = [
        MCPServerConfig(
            name="fs_tmp",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        ),
        MCPServerConfig(
            name="fs_home",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/Users"],
        ),
    ]
    
    try:
        # 连接所有 Server
        for config in servers:
            print(f"\n连接 {config.name}...")
            await client.connect(config)
            print(f"  ✅ 已连接")
        
        # 列出所有工具
        print(f"\n共连接 {len(client.list_connections())} 个 Server")
        print(f"共有 {len(client.list_tools())} 个工具")
        
        # 获取所有 LangChain 工具
        lc_tools = client.get_langchain_tools()
        print(f"转换为 {len(lc_tools)} 个 LangChain 工具")
        
        # 显示工具名称（注意前缀区分）
        print("\n工具名称示例:")
        for tool in lc_tools[:6]:
            print(f"  - {tool.name}")
        
    finally:
        await client.disconnect_all()


async def main():
    """主函数"""
    
    print("\n请确保已创建测试文件: echo 'Hello MCP' > /tmp/test.txt\n")
    
    # 运行基础测试
    await test_mcp_client_service()
    
    # 询问是否运行多 Server 测试
    # choice = input("\n是否测试多 Server 连接? (y/n): ").strip().lower()
    # if choice == 'y':
    #     await test_multiple_servers()


if __name__ == "__main__":
    asyncio.run(main())
