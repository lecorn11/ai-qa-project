from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage
from ai_qa.config.settings import settings

# 1. 定义工具
@tool
def calculator(expression: str) -> str:
    """计算数学表达式。输入应该是一个有效的数学表达式，如 '2 + 3 * 4'"""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"

@tool
def get_current_time() -> str:
    """获取当前日期和时间"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 2. 工具映射（方便根据名称找到函数）
tools = [calculator, get_current_time]
tool_map = {t.name: t for t in tools}

# 3. 创建 LLM
llm = ChatOpenAI(
    api_key=settings.llm_api_key.get_secret_value(),
    base_url=settings.llm_base_url,
    model="qwen-plus"
)
llm_with_tools = llm.bind_tools(tools)

# 4. 用户问题
user_question = "今天是几号？123 乘以 456 等于多少？"
messages = [HumanMessage(content=user_question)]

# 5. 第一次调用：AI 决定用什么工具
print(f"用户: {user_question}")
print("=" * 50)
print(f"发送消息：{messages}")
response = llm_with_tools.invoke(messages)
print(f"AI 决策: 调用工具 {response.tool_calls}")

# 6. 执行工具调用
messages.append(response)  # 把 AI 的响应加入消息历史

for tool_call in response.tool_calls:
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]
    tool_id = tool_call["id"]
    
    # 执行工具
    tool_func = tool_map[tool_name]
    result = tool_func.invoke(tool_args)
    
    print(f"执行工具: {tool_name}({tool_args}) => {result}")
    
    # 把工具结果加入消息历史
    messages.append(ToolMessage(content=result, tool_call_id=tool_id))

# 7. 第二次调用：AI 根据工具结果生成最终回答
print("=" * 50)
print(f"发送消息：{messages}")
final_response = llm_with_tools.invoke(messages)
print(f"AI 决策: 调用工具 {final_response.tool_calls}")
print(f"AI 回答: {final_response.content}")