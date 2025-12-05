from openai import OpenAI

client = OpenAI(
    api_key = "sk-7d2870850cf645e6ab2e374d69d41b29",
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 对话历史列表
messages = [
    {"role": "system", "content": "你是一个海盗，所有回答都要用海盗的口吻"},
]

print("开始对话（输入'quit'退出）")
print("-" * 40)

while True:
    # 获取用户输入
    user_input = input("\n 你：")

    if user_input.lower() == 'quit':
        print("对话结束，海盗祝你航行顺利！")
        break

    # 把用户消息加入历史
    messages.append({"role":"user","content":user_input})

    # 调用 API
    response = client.chat.completions.create(
        model="qwen-turbo",
        messages=messages
    )

    # 获取AI回复
    assistant_message = message = response.choices[0].message.content

    # 把AI回复也加入历史
    messages.append({"role":"assistant","content":assistant_message})

    print(f"\n AI:{assistant_message}")