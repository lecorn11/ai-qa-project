from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from ai_qa.domain.entities import Message, MessageRole
from ai_qa.infrastructure.llm.base import BaseLLMAdapter


class QwenAdapter(BaseLLMAdapter):
    """通义千问适配器"""

    def __init__(self, api_key: str, base_url: str, model_name: str):
        super().__init__(api_key, base_url, model_name)

        # 创建 LangChain 的 ChatOpenAI 实例
        self._client = ChatOpenAI(
            api_key = self.api_key,
            base_url = self.base_url,
            model = self.model_name
        )

    def chat(self, messages: list[Message], system_prompt: str = None) -> str:
        """发送消息并获取回复"""

        # 转换为 LangChain 消息格式
        langchain_messages = []

        # 添加系统提示
        if system_prompt:
            langchain_messages.append(SystemMessage(content=system_prompt))
        
        # 转换消息列表
        for msg in messages:
            if msg.role == MessageRole.USER:
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == MessageRole.ASSISTANT:
                langchain_messages.append(AIMessage(content=msg.content))
            elif msg.role == MessageRole.SYSTEM:
                langchain_messages.append(SystemMessage(content=msg.content))
        
        # 调用 API
        response = self._client.invoke(langchain_messages)

        return response.content