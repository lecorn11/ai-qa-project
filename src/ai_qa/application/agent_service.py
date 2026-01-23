import json
import logging
from typing import AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from ai_qa.domain.entities import Conversation, MessageRole
from ai_qa.domain.ports import ConversationMemoryPort, LLMPort

logger = logging.getLogger(__name__)

REACT_SYSTEM_PROMPT = """你是一个智能助手，可以使用工具来帮助回答问题。

## 工作方式
你需要按照「思考 → 行动 → 观察」的模式来解决问题：

1. **思考**：分析用户的问题，思考下一步该怎么做
2. **行动**：如果需要，调用合适的工具
3. **观察**：查看工具返回的结果，继续思考
4. 重复以上步骤，直到能够给出最终答案

## 重要规则
- 每次回复时，你必须先输出你的思考过程
- 思考内容用 [思考] 开头，单独一行
- 即使你决定调用工具，也要先说明为什么要调用这个工具
- 思考要简洁，1-2 句话即可
- **当本轮需要调用多个工具时，在“行动”之前，[思考] 必须一次性写清楚“本轮计划调用的所有工具清单（按顺序）+ 每个工具的目的/原因”。不得只写第一个工具。**
- **如果你预期需要分多轮调用工具（例如先查A再决定是否查B），也必须在 [思考] 里说明“当前先调用哪个工具 + 后续可能调用哪些工具及触发条件”。**


## 输出格式示例

示例 1 - 需要调用工具：
[思考] 用户想要计算 123 × 456，我需要使用计算器工具来确保准确性。

示例 2 - 需要调用多个工具（同一轮）：
[思考] 用户想要计算 123 × 456 并查询日期；本轮我将先用计算器确保乘法准确，然后用时间查询工具获取当前日期。

示例 3 - 需要分多轮调用工具（有条件）：
[思考] 用户想要找某政策的最新信息；本轮先用网页搜索工具确认最新版本与发布日期，如搜索结果不完整再打开权威来源页面进一步核对细节。

示例 4 - 观察工具结果后：
[思考] 计算器返回了 56088，现在我可以回答用户了。

示例 5 - 不需要工具：
[思考] 这是一个简单的问候，不需要使用任何工具。
你好！有什么我可以帮助你的吗？
"""

class AgentService:
    """Agent 服务 - 支持工具调用的智能对话"""

    def __init__(
            self,
            llm: LLMPort,
            memory: ConversationMemoryPort,
            tools: list = None,
            system_prompt: str = None
    ):
        self._llm = llm
        self._memory = memory
        self._tools = tools or []
        self._system_prompt = system_prompt or REACT_SYSTEM_PROMPT

        # 构建工具映射
        self._tool_map = {tool.name: tool for tool in self._tools}

    async def chat(self, session_id: str, user_input: str, user_id: str = None, extra_tools: list = None) -> str:
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
        final_response = await self._agent_loop(messages,extra_tools)

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
    
    async def _agent_loop(self, messages: list, extra_tools: list = None ,max_iterations: int = 10) -> str:
        """
        Agent 循环: 不断调用 LLM 直到不需要工具

        Args: 
            nmessages: 消息列表
            max_iterations: 最大迭代次数
        
        Returns:
            最终回复内容
        """

        # 整合工具
        all_tools, tool_map = self._get_tools_and_map(extra_tools)

        for _ in range(max_iterations):
            # 调用 LLM
            response = self._llm.chat_with_tools(
                messages=messages,
                tools=all_tools,
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
                if tool_name in tool_map:
                    tool_func = tool_map[tool_name]
                    result = await tool_func.ainvoke(tool_args)
                else:
                    result = f"错误：未知工具{tool_name}"
                
                # 把工具结果加入到消息历史
                messages.append(ToolMessage(content=str(result), tool_call_id = tool_id))
            
        # 超过最大迭代次数
        return "抱歉，处理过程过于复杂，请简化您的问题。"
    
    async def chat_stream(
        self,
        session_id: str,
        user_input: str,
        user_id: str = None,
        extra_tools: list = None
    ) -> AsyncGenerator[str, None]:
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
        
        async for event in self._agent_loop_stream(messages,extra_tools):
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
    
    async def _agent_loop_stream(
        self,
        messages: list,
        extra_tools: list = None,
        max_iterations: int = 10
    ) -> AsyncGenerator[str, None]:
        """Agent 循环编排（流式版本）"""

        all_tools, tool_map = self._get_tools_and_map(extra_tools)
        iteration = 0

        for iteration in range(max_iterations):
            # 调用 LLM
            response = self._llm.chat_with_tools(
                messages=messages,
                tools=all_tools,
                system_prompt=self._system_prompt
            )
            if response.content:
                thinking_content = self._extract_thinking(response.content)
                if thinking_content:
                    yield self._sse_event({
                        "type": "thinking",
                        "content": thinking_content,
                        "iteration": iteration + 1
                    })
            logger.info(f"Agent 工具调用响应: {response.content} Tool Calls: {response.tool_calls}")

            # 添加 AI 响应到消息历史
            messages.append(response)

            # 如果没有工具调用，返回最终回答
            if not response.tool_calls:
                # 提取最终答案（过滤掉思考部分）
                final_answer = self._extract_final_answer(response.content)

                if final_answer:
                    yield self._sse_event({"type": "answer", "content": final_answer})
                yield self._sse_event({"type": "done"})
                return
        
            # 有工具调用，执行工具调用
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
                if tool_name in tool_map:
                    tool_func = tool_map[tool_name]
                    result = await tool_func.ainvoke(tool_args)
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
    
    def _extract_thinking(self, content: str) -> str:
        """ 从 LLM 响应中提取思考内容"""
        if not content:
            return ""
        
        lines = content.strip().split('\n')
        thinking_lines = []

        for line in lines:
            # 匹配 [思考] 开头的行
            if line.strip().startswith("[思考]"):
                thinking = line.strip().replace("[思考]", "").strip()
                thinking_lines.append(thinking)

        return " ".join(thinking_lines)
    
    def _extract_final_answer(self, content: str) -> str:
        """ 从 LLM 响应中提取最终答案（非思考部分）"""
        if not content:
            return ""
        
        lines = content.strip().split('\n')
        answer_lines = []

        for line in lines:
            # 匹配 [思考] 开头的行
            if not line.strip().startswith("[思考]"):
                answer_lines.append(line)

        return " ".join(answer_lines).strip()
                        

    def _sse_event(self, data: dict) -> str:
        """格式化为 SSE 事件"""
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    
    def _get_tools_and_map(self, extra_tools=None):
        """合并内置工具和额外工具，返回工具列表和映射"""
        all_tools = self._tools + (extra_tools or [])
        tool_map = {tool.name: tool for tool in all_tools}
        return all_tools, tool_map
