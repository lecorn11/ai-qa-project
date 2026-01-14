import asyncio
import sys
sys.path.insert(0, "src")

from ai_qa.infrastructure.mcp.client import (
    MCPClientService,
    MCPServerConfig,
    FILESYSTEM_SERVER,
)

async def test_langchain_tool_async():
    """全异步测试"""
    client = MCPClientService()
    
    try:
        await client.connect(FILESYSTEM_SERVER)
        
        lc_tools = client.get_langchain_tools()
        read_tool = next(t for t in lc_tools if "read_file" in t.name)
        
        # 使用 ainvoke（异步调用）
        result = await read_tool.ainvoke({"path": "/tmp/test.txt"})
        print(f"结果: {result}")
        
    finally:
        await client.disconnect_all()

if __name__ == "__main__":
    asyncio.run(test_langchain_tool_async())