"""ChatService 单元测试"""
from ai_qa.application.chat_service import ChatService
from ai_qa.domain.entities import Conversation, MessageRole

class TestChatService:
    """ChatService 测试类"""

    def test_chat_returns_llm_response(self, mock_llm, mock_memory):
        """测试：chat 方法应返回 LLM 的回复"""
        # Arrange（准备）
        service = ChatService(llm=mock_llm, memory=mock_memory)

        # Act（执行）
        result = service.chat("test_session", "你好")

        # Assert（验证）
        assert result == "这是 AI 的回复"
    
    def test_chat_saves_conversation(self, mock_llm, mock_memory):
        """测试：chat 后应保存对话历史"""
        # Arrange（准备）
        service = ChatService(llm=mock_llm, memory=mock_memory)

        # Act（执行）
        service.chat("test_session", "你好")

        # Assert（验证）save_conversation  被调用了
        mock_memory.save_conversation.assert_called_once()

    def test_chat_adds_user_and_assistant_messages(self, mock_llm, mock_memory):
        """测试：chat 应添加用户消息和 AI 消息到对话"""
        # Arrange
        conversation = Conversation(id="test_session")
        mock_memory.get_conversation.return_value = conversation
        service = ChatService(llm=mock_llm, memory=mock_memory)

        # Act
        service.chat("test_session", "你好")

        # Assert: 对话中应有2条信息
        assert len(conversation.messages) == 2
        assert conversation.messages[0].role == MessageRole.USER
        assert conversation.messages[0].content == "你好"
        assert conversation.messages[1].role == MessageRole.ASSISTANT
        assert conversation.messages[1].content == "这是 AI 的回复"
    
    def test_chat_passes_system_prompt_to_llm(self, mock_llm, mock_memory):
        """测试：chat 应将 system_propt 传给 LLM"""
        # Arrange
        custom_prompt = "你是一个海盗"
        service = ChatService(llm=mock_llm, memory=mock_memory, system_prompt=custom_prompt)

        # Act
        service.chat("test_session", "你好")

        # Assert: 验证 LLM 被调用时传入了正确的 system_prompt
        mock_llm.chat.assert_called_once()
        call_kwargs = mock_llm.chat.call_args.kwargs
        assert call_kwargs["system_prompt"] == custom_prompt