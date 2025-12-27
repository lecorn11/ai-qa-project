from openai import OpenAI
from ai_qa.config.settings import settings

client = OpenAI(
    api_key = settings.llm_api_key,
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
)

response = client.chat.completions.create(
    model="qwen-turbo",
    messages=[
        {"role": "system", "content": "你是一个海盗，所有回答都要用海盗的口吻"},
        {"role": "user", "content": "你是谁？"}
    ]
)
print(response.choices[0].message.content)