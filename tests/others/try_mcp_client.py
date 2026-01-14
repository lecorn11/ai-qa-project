"""
MCP Client 基础测试

测试目标：
1. 连接到 MCP Server
2. 列出可用工具
3. 调用工具

运行前准备：
1. 确保安装了 mcp: pip install mcp
2. 准备测试文件: echo "Hello MCP" > /tmp/test.txt
3. 安装 filesystem server: npm install -g @modelcontextprotocol/server-filesystem
   或者使用 npx 临时运行（脚本默认使用 npx）
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_filesystem_server():
    """测试官方 filesystem MCP Server"""
    
    print("=" * 50)
    print("测试 MCP Client - Filesystem Server")
    print("=" * 50)
    
    # 1. 定义 Server 连接参数
    # 使用 npx 临时运行 filesystem server，允许访问 /tmp 目录
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    )
    
    print("\n[1] 正在连接 Filesystem Server...")
    print(f"    命令: {server_params.command} {' '.join(server_params.args)}")
    
    try:
        # 2. 建立连接
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                
                # 3. 初始化握手
                print("\n[2] 初始化连接...")
                init_result = await session.initialize()
                print(f"    服务器: {init_result.serverInfo.name} v{init_result.serverInfo.version}")
                
                # 4. 获取工具列表
                print("\n[3] 获取可用工具列表...")
                tools_result = await session.list_tools()
                
                print(f"\n    发现 {len(tools_result.tools)} 个工具:")
                for tool in tools_result.tools:
                    print(f"    📌 {tool.name}")
                    print(f"       描述: {tool.description[:60]}..." if len(tool.description) > 60 else f"       描述: {tool.description}")
                    # 打印参数信息
                    if tool.inputSchema and "properties" in tool.inputSchema:
                        params = list(tool.inputSchema["properties"].keys())
                        print(f"       参数: {params}")
                    print()
                
                # 5. 调用工具 - 读取文件
                print("\n[4] 测试调用工具: read_file")
                print("    读取文件: /tmp/test.txt")
                
                try:
                    result = await session.call_tool(
                        name="read_file",
                        arguments={"path": "/tmp/test.txt"}
                    )
                    print(f"    ✅ 调用成功!")
                    print(f"    结果: {result.content}")
                except Exception as e:
                    print(f"    ❌ 调用失败: {e}")
                    print("    提示: 请先创建测试文件 - echo 'Hello MCP' > /tmp/test.txt")
                
                # 6. 调用工具 - 列出目录
                print("\n[5] 测试调用工具: list_directory")
                print("    列出目录: /tmp")
                
                try:
                    result = await session.call_tool(
                        name="list_directory",
                        arguments={"path": "/tmp"}
                    )
                    print(f"    ✅ 调用成功!")
                    # 只显示前5个文件
                    content = str(result.content)
                    print(f"    结果（部分）: {content[:200]}..." if len(content) > 200 else f"    结果: {content}")
                except Exception as e:
                    print(f"    ❌ 调用失败: {e}")
                
                print("\n" + "=" * 50)
                print("测试完成!")
                print("=" * 50)
                
    except FileNotFoundError:
        print("\n❌ 错误: 找不到 npx 命令")
        print("   请确保已安装 Node.js: https://nodejs.org/")
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        raise


async def test_our_server():
    """测试我们自己的 MCP Server"""
    
    print("=" * 50)
    print("测试 MCP Client - 我们的知识库 Server")
    print("=" * 50)
    
    # 连接到我们自己的 MCP Server
    # 注意：需要根据你的实际路径修改
    server_params = StdioServerParameters(
        command="/opt/homebrew/Caskroom/miniforge/base/envs/ai-qa/bin/python",
        args=["-m", "ai_qa.infrastructure.mcp.server"],
        cwd="/Users/lecorn/Projects/ai-qa-project",  # 项目根目录
        env={
            "PYTHONPATH": "/Users/lecorn/Projects/ai-qa-project/src"
        }
    )
    
    print("\n[1] 正在连接我们的 MCP Server...")
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                
                # 初始化
                print("\n[2] 初始化连接...")
                init_result = await session.initialize()
                print(f"    服务器: {init_result.serverInfo.name}")
                
                # 获取工具
                print("\n[3] 获取可用工具...")
                tools_result = await session.list_tools()
                
                print(f"\n    发现 {len(tools_result.tools)} 个工具:")
                for tool in tools_result.tools:
                    print(f"    📌 {tool.name}: {tool.description}")
                
                # 获取资源
                print("\n[4] 获取可用资源...")
                resources_result = await session.list_resources()
                
                print(f"\n    发现 {len(resources_result.resources)} 个资源:")
                for resource in resources_result.resources:
                    print(f"    📚 {resource.uri}: {resource.name}")
                
                print("\n" + "=" * 50)
                print("测试完成!")
                print("=" * 50)
                
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        print("   请检查路径配置是否正确")
        raise


async def main():
    """主函数 - 选择测试哪个 Server"""
    
    print("\n选择要测试的 MCP Server:")
    print("1. 官方 Filesystem Server (推荐先测试这个)")
    print("2. 我们的知识库 Server")
    print()
    
    choice = input("请输入选项 (1/2): ").strip()
    
    if choice == "1":
        await test_filesystem_server()
    elif choice == "2":
        await test_our_server()
    else:
        print("无效选项，默认测试 Filesystem Server")
        await test_filesystem_server()


if __name__ == "__main__":
    asyncio.run(main())