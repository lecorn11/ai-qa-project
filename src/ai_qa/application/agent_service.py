


import json
import logging
from typing import Generator
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from ai_qa.domain.entities import Conversation, MessageRole
from ai_qa.domain.ports import ConversationMemoryPort, LLMPort

logger = logging.getLogger(__name__)

class AgentService:
    """Agent 服务 - 支持工具调用的智能对话"""

    def __init__(
            self,
            llm: LLMPort,
            memory: ConversationMemoryPort,
            tools: list = None,
            system_prompt: str = "你是一个智能助手，可以使用工具来帮助回答问题。"
    ):
        self._llm = llm
        self._memory = memory
        self._tools = tools or []
        self._system_prompt = system_prompt

        # 构建工具映射
        self._tool_map = {tool.name: tool for tool in self._tools}

    def chat(self, session_id: str, user_input: str, user_id: str = None) -> str:
        """
        处理用户输入，自动决定是否调用工具
        
        Args:
            session_id: 会话 ID
            user_input: 用户输入
            user_id: 用户 ID
        
        Returns:
            AI 的最终回复
        """
        
        logger.info(
            f"Agent 对话处理开始 session_id={session_id} user_id={user_id} user_input={user_input}"
        )

        # 1. 获取对话历史
        conversation = self._memory.get_conversation(session_id, user_id=user_id)

        # 2. 构建消息列表
        messages = self._build_messages(conversation, user_input)

        # 3. Agent 循环调用工具直到有最终回答
        final_response = self._agent_loop(messages)

        # 4. 保存历史对话
        conversation.add_message(MessageRole.USER, user_input)
        conversation.add_message(MessageRole.ASSISTANT, final_response)
        self._memory.save_conversation(conversation)

        logger.info(
            f"Agent 对话处理完成 session_id={session_id} user_id={user_id} ai_response={final_response}"
        )

        return final_response
    
    def _build_messages(self, conversation: Conversation, user_input: str) -> list:
        """构建 LangChain 消息列表"""
        messages = []

        # 添加历史消息
        for msg in conversation.messages:
            if msg.role == MessageRole.USER:
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == MessageRole.ASSISTANT:
                messages.append(AIMessage(content=msg.content))
        
        # 添加当前用户输入
        messages.append(HumanMessage(content=user_input))

        return messages
    
    def _agent_loop(self, messages: list, max_iterations: int = 10) -> str:
        """
        Agent 循环: 不断调用 LLM 直到不需要工具

        Args: 
            nmessages: 消息列表
            max_iterations: 最大迭代次数
        
        Returns:
            最终回复内容
        """
        for _ in range(max_iterations):
            # 调用 LLM
            response = self._llm.chat_with_tools(
                messages=messages,
                tools=self._tools,
                system_prompt=self._system_prompt
            )

            # 如果没有工具调用，返回最终回答
            if not response.tool_calls:
                return response.content
        
            # 有工具调用，添加 AI 响应到消息历史
            messages.append(response)

            # 执行工具调用
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]
            
                # 查找并执行工具
                if tool_name in self._tool_map:
                    tool_func = self._tool_map[tool_name]
                    result = tool_func.invoke(tool_args)
                else:
                    result = f"错误：未知工具{tool_name}"
                
                # 把工具结果加入到消息历史
                messages.append(ToolMessage(content=str(result), tool_call_id = tool_id))
            
        # 超过最大迭代次数
        return "抱歉，处理过程过于复杂，请简化您的问题。"
    

    def chat_stream(
        self,
        session_id: str,
        user_input: str,
        user_id: str = None
    ) -> Generator[str, None, None]:
        """流式处理用户输出，返回 SSE 格式的消息流
        
        消息类型：
        - tool_start: 开始调用工具
        - tool_result: 工具返回结果  
        - answer: 最终回答（流式）
        - done: 完成
        """
        logger.info(
            f"Agent 流式对话开始 session_id={session_id} user_id={user_id}"
        )

        # 1. 获取对话历史
        conversation = self._memory.get_conversation(session_id, user_id=user_id)

        # 2. 构建消息列表
        messages = self._build_messages(conversation, user_input)

        # 3. Agent 循环调用工具直到有最终回答
        full_response = ""
        
        for event in self._agent_loop_stream(messages):
            yield event

            # 收集最终回答内容（用于保存历史）
            try:
                event_data = event.replace("data: ", "").strip()
                if event_data:
                    data = json.loads(event_data)
                    if data.get("type") == "answer":
                        full_response += data.get("content","")
            except:
                pass
        


        # 4. 保存历史对话
        conversation.add_message(MessageRole.USER, user_input)
        if full_response:
            conversation.add_message(MessageRole.ASSISTANT, full_response)
        self._memory.save_conversation(conversation)

        logger.info(
            f"Agent 流式对话完成 session_id={session_id} user_id={user_id} ai_response={full_response}"
        )
    
    def _agent_loop_stream(
        self,
        messages: list,
        max_iterations: int = 10
    ) -> Generator[str, None, None]:
        """Agent 循环编排（流式版本）"""

        for _ in range(max_iterations):
            # 调用 LLM
            response = self._llm.chat_with_tools(
                messages=messages,
                tools=self._tools,
                system_prompt=self._system_prompt
            )

            # 如果没有工具调用，返回最终回答
            if not response.tool_calls:
                for chunk in self._llm.chat_stream(messages, self._system_prompt):
                    yield self._sse_event({"type":"answer","content":chunk})
                yield self._sse_event({"type": "done"})
                return
        
            # 有工具调用，添加 AI 响应到消息历史
            messages.append(response)

            # 执行工具调用
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]
            
                # 发送 tool_start 事件
                yield self._sse_event({
                    "type": "tool_start",
                    "tool": tool_name,
                    "input": json.dumps(tool_args, ensure_ascii=False)
                })

                # 查找并执行工具
                if tool_name in self._tool_map:
                    tool_func = self._tool_map[tool_name]
                    result = tool_func.invoke(tool_args)
                else:
                    result = f"错误：未知工具{tool_name}"
                
                # 发送 tool_result 事件
                yield self._sse_event({
                    "type": "tool_result",
                    "tool": tool_name,
                    "output": str(result)
                })

                # 把工具结果加入到消息历史
                messages.append(ToolMessage(content=str(result), tool_call_id = tool_id))
            
        # 超过最大迭代次数
        yield self._sse_event({
            "type": "answer",
            "content": "抱歉，处理过程过于复杂，请简化您的问题。"
        })
        yield self._sse_event({"type":"done"})
    
    def _sse_event(self, data: dict) -> str:
        """格式化为 SSE 事件"""
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        



