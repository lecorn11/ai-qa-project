import logging
from typing import Generator
from ai_qa.domain.entities import MessageRole
from ai_qa.domain.ports import LLMPort, ConversationMemoryPort

logger = logging.getLogger(__name__)


class ChatService:
    """聊天服务（应用层）

    编排领域逻辑，协调 LLM 和记忆存储
    """

    def __init__(
        self,
        llm: LLMPort,
        memory: ConversationMemoryPort,
        system_prompt: str = "你是一个友好的助手，回答尽量简洁。",
    ):
        self._llm = llm
        self._memory = memory
        self._system_prompt = system_prompt

    def chat(self, session_id: str, user_input: str, user_id: str = None) -> str:
        """处理用户输入并返回 AI 回复

        Args:
            session_id: 会话 ID
            user_input: 用户输入内容
            user_id:    用户 ID

        Returns:
            AI 回复内容
        """
        logger.info(
            f"消息对话处理开始 session_id={session_id} user_id={user_id} user_input={user_input}"
        )

        # 1. 获取对话历史
        conversation = self._memory.get_conversation(session_id, user_id=user_id)

        # 2. 添加用户消息
        conversation.add_message(MessageRole.USER, user_input)

        # 3. 调用 LLM 获取回复
        response = self._llm.chat(
            messages=conversation.messages, system_prompt=self._system_prompt
        )

        # 4. 添加 AI 回复到历史中
        conversation.add_message(MessageRole.ASSISTANT, response)

        # 5. 保存对话历史
        self._memory.save_conversation(conversation)

        logger.info(
            f"消息对话处理完成 session_id={session_id} user_id={user_id} ai_response={response}"
        )

        return response

    def chat_stream(
        self, session_id: str, user_input: str, user_id: str = None
    ) -> Generator:
        """处理用户输入，流式返回 AI 回复

        Args:
            session_id: 会话 ID
            user_input: 用户输入内容
            user_id:    用户 ID

        Returns:
            AI 回复内容
        """
        logger.info(
            f"流式对话处理开始 session_id={session_id} user_id={user_id} user_input={user_input}"
        )

        # 1. 获取对话历史
        conversation = self._memory.get_conversation(session_id, user_id=user_id)

        # 2. 添加用户消息
        conversation.add_message(MessageRole.USER, user_input)

        # 3. 调用 LLM 流式接口，获取回复
        full_response = ""
        try:
            for chunk in self._llm.chat_stream(
                messages=conversation.messages, system_prompt=self._system_prompt
            ):
                full_response += chunk
                yield chunk
        except Exception as e:
            logger.error(
                f"流式对话异常 session_id = {session_id} error = {str(e)} response_length = {len(full_response)}"
            )
            raise
        finally:
            if full_response:
                # 4. 添加 AI 完整（或部分）回复到历史中
                conversation.add_message(MessageRole.ASSISTANT, full_response)
                # 5. 保存对话历史
                self._memory.save_conversation(conversation)

            logger.info(f"流式对话处理完成 session_id={session_id}")

    def set_system_prompt(self, prompt: str) -> None:
        """设置系统提示词"""
        self._system_prompt = prompt
