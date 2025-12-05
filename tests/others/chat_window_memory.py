from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage,trim_messages
from langchain_core.chat_history import InMemoryChatMessageHistory

# 创建 CHat 模型
chat = ChatOpenAI(
    api_key="sk-7d2870850cf645e6ab2e374d69d41b29",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model_name="qwen-turbo"
)

# 消息修剪器：保留最近的消息，最多200tokens
trimmer = trim_messages(
    max_tokens=200,
    strategy="last",
    token_counter=len,
    include_system=True,
    start_on="human",
)

# 系统消息
system_message = SystemMessage(content="你是一个海盗，所有回答都要用海盗的口吻")
messages = [system_message]

print("开始对话（输入'quit'退出）")
print("（只会保留最近的对话，早期对话会被遗忘）")
print("-" * 40)

while True:
    user_input = input("\n 你：")

    if user_input.lower() == 'quit':
        print("对话结束，海盗祝你航行顺利！")
        break   
    # 添加用户消息
    messages.append({"role": "user", "content": user_input})
    
    # 修剪消息，只保留最近的
    trimmed = trimmer.invoke(messages)
    
    # 打印当前保留了多少消息（方便观察）
    print(f"  [当前历史消息数: {len(trimmed)}]")
    
    # 调用 API
    response = chat.invoke(trimmed)
    
    # 添加 AI 回复
    messages.append({"role": "assistant", "content": response.content})
    
    print(f"\nAI: {response.content}")