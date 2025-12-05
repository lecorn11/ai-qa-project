from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# 创建 CHat 模型
chat = ChatOpenAI(
    api_key="sk-7d2870850cf645e6ab2e374d69d41b29",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model_name="qwen-turbo"
)

# LangChain 用类来表示信息，而不是字典
message = [
    SystemMessage(content = "你是一个海盗，所有回答都要用海盗的口吻"),
    HumanMessage(content = "今天天气怎么样？")
]

# 调用
response = chat.invoke(message)
print(response.content)