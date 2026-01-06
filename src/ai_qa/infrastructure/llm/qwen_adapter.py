from typing import Generator
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from ai_qa.domain.entities import Message, MessageRole
from ai_qa.infrastructure import llm
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

        # 创建流式客户端
        self._stream_client = ChatOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model_name,
            streaming=True
        )

    def _conver_message(self, messages: list[Message], system_prompt: str = None) -> list:
        # 把消息转换为 LangChain 格式
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
        
        return langchain_messages
    
    def chat(self, messages: list[Message], system_prompt: str = None) -> str:
        """发送消息并获取回复"""
        langchain_messages = self._conver_message(messages, system_prompt)
        response = self._client.invoke(langchain_messages)
        return response.content
    
    def chat_stream(self, messages: list[Message], system_prompt: str = None) -> Generator[str, None, None]:
        """流式发送消息，逐步返回回复"""
        langchain_messages = self._conver_message(messages, system_prompt)

        for chunk in self._stream_client.stream(langchain_messages):
            if chunk.content:
                yield chunk.content
    
    def chat_with_tools(self, messages: list[Message], tools: list, system_prompt: str = None) -> Generator[str, None, None]:
        """支持工具调用的对话"""
        # 如果有系统提示词，添加到消息开头
        if system_prompt:
            messages = [SystemMessage(content=system_prompt)] + messages
        
        # 绑定工具到 LLM
        if tools:
            llm_with_tools = self._client.bind_tools(tools)
        else:
            llm_with_tools = self._client
        
        # 调用并返回完整的 AIMessage
        response = llm_with_tools.invoke(messages)
        return response