from ai_qa.config.settings import settings
from ai_qa.infrastructure.llm.qwen_adapter import QwenAdapter
from ai_qa.infrastructure.memory.in_memory import InMemoryConversationMemory
from ai_qa.infrastructure.tools import calculator, get_current_time
from ai_qa.application.agent_service import AgentService

# 1. 创建基础设施
llm = QwenAdapter(
    api_key=settings.llm_api_key.get_secret_value(),
    base_url=settings.llm_base_url,
    model_name="qwen-plus"  # 需要用 qwen-plus 支持 function calling
)

memory = InMemoryConversationMemory()

# 2. 创建 Agent 服务
agent = AgentService(
    llm=llm,
    memory=memory,
    tools=[calculator, get_current_time],
    system_prompt="你是一个智能助手，可以使用计算器和时间工具来帮助回答问题。"
)

# 3. 测试
print("=" * 50)
print("测试 1：计算问题")
print("=" * 50)
response = agent.chat("test_session", "123 乘以 456 等于多少？")
print(f"回答: {response}")

print("\n" + "=" * 50)
print("测试 2：时间问题")
print("=" * 50)
response = agent.chat("test_session", "现在几点了？")
print(f"回答: {response}")

print("\n" + "=" * 50)
print("测试 3：混合问题")
print("=" * 50)
response = agent.chat("test_session", "今天是几号？另外帮我算一下 2 的 10 次方")
print(f"回答: {response}")

print("\n" + "=" * 50)
print("测试 4：普通问题（不需要工具）")
print("=" * 50)
response = agent.chat("test_session", "你好，介绍一下你自己")
print(f"回答: {response}")