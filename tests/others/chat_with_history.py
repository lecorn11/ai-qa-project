from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# 1. 创建 Chat 模型
model = ChatOpenAI(
    api_key="sk-7d2870850cf645e6ab2e374d69d41b29",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-turbo"
)

# 2. 创建 Prompt 模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个海盗，所有回答都要用海盗的口吻"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

# 3. 构建 Chain（使用 LCEL 管道语法）
chain = prompt | model

# 4. 存储不同会话的历史记录（key 是 session_id)
store = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# 5. 用 RunableWithMessageHistory 包装 chain
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)


# 6. 开始对话
print("开始对话（输入'quit'退出）")
print("-" * 40)

# 假设 session_id 是固定的 "session_1"
session_id = "user_123"

while True:
    user_input = input("\n 你：")

    if user_input.lower() == 'quit':
        print("对话结束，海盗祝你航行顺利！")
        break   

    # 调用带有历史的 chain
    response = chain_with_history.invoke(
        {"input": user_input},
        config={"configurable": {"session_id": session_id}},
    )

    print(f"\n AI:{response.content}")