from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.chat_history import InMemoryChatMessageHistory

# 创建 Chat 模型
chat = ChatOpenAI(
    api_key="sk-7d2870850cf645e6ab2e374d69d41b29",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model_name="qwen-turbo"
)


# 使用 LangChain 的消息历史管理
history = InMemoryChatMessageHistory()

# 系统消息
system_message = SystemMessage(content="你是一个海盗，所有回答都要用海盗的口吻")

print("开始对话（输入'quit'退出）")
print("-" * 40)

while True:
    user_input = input("\n 你：")

    if user_input.lower() == 'quit':
        print("对话结束，海盗祝你航行顺利！")
        break   

    # 添加用户消息到历史
    history.add_user_message(user_input)

    # 构建完整消息列表：系统消息 + 历史记录
    messages = [system_message] + history.messages

    # 调用 API
    response = chat.invoke(messages)

    # 添加 AI 回复到历史中
    history.add_ai_message(response.content)
    print(f"\n AI:{response.content}")