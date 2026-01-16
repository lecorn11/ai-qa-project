"""QwenAdapter 单元测试"""
import pytest
from unittest.mock import MagicMock, patch, Mock
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from ai_qa.infrastructure.llm.qwen_adapter import QwenAdapter
from ai_qa.domain.entities import Message, MessageRole


@pytest.fixture
def qwen_adapter():
    """创建 QwenAdapter 实例"""
    with patch('ai_qa.infrastructure.llm.qwen_adapter.ChatOpenAI') as mock_chat_openai:
        adapter = QwenAdapter(
            api_key="test_api_key",
            base_url="https://test.api.com",
            model_name="qwen-test"
        )
        # 保存 mock 客户端以便后续访问
        adapter._mock_client = mock_chat_openai.return_value
        adapter._mock_stream_client = mock_chat_openai.return_value
        yield adapter


class TestQwenAdapterInitialization:
    """QwenAdapter 初始化测试"""

    def test_init_creates_clients(self):
        """测试：初始化创建客户端实例"""
        with patch('ai_qa.infrastructure.llm.qwen_adapter.ChatOpenAI') as mock_chat_openai:
            # Act
            adapter = QwenAdapter(
                api_key="test_key",
                base_url="https://api.test.com",
                model_name="qwen-max"
            )

            # Assert
            assert adapter.api_key == "test_key"
            assert adapter.base_url == "https://api.test.com"
            assert adapter.model_name == "qwen-max"
            # 验证 ChatOpenAI 被调用了两次（普通客户端和流式客户端）
            assert mock_chat_openai.call_count == 2


class TestConvertMessage:
    """消息转换功能测试"""

    def test_convert_message_user_message(self, qwen_adapter):
        """测试：转换用户消息"""
        # Arrange
        messages = [Message(role=MessageRole.USER, content="Hello")]

        # Act
        result = qwen_adapter._conver_message(messages)

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], HumanMessage)
        assert result[0].content == "Hello"

    def test_convert_message_assistant_message(self, qwen_adapter):
        """测试：转换助手消息"""
        # Arrange
        messages = [Message(role=MessageRole.ASSISTANT, content="Hi there")]

        # Act
        result = qwen_adapter._conver_message(messages)

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], AIMessage)
        assert result[0].content == "Hi there"

    def test_convert_message_system_message(self, qwen_adapter):
        """测试：转换系统消息"""
        # Arrange
        messages = [Message(role=MessageRole.SYSTEM, content="You are a helpful assistant")]

        # Act
        result = qwen_adapter._conver_message(messages)

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], SystemMessage)
        assert result[0].content == "You are a helpful assistant"

    def test_convert_message_with_system_prompt(self, qwen_adapter):
        """测试：带系统提示词的消息转换"""
        # Arrange
        messages = [Message(role=MessageRole.USER, content="Hello")]
        system_prompt = "You are an AI assistant"

        # Act
        result = qwen_adapter._conver_message(messages, system_prompt)

        # Assert
        assert len(result) == 2
        assert isinstance(result[0], SystemMessage)
        assert result[0].content == system_prompt
        assert isinstance(result[1], HumanMessage)
        assert result[1].content == "Hello"

    def test_convert_message_multiple_messages(self, qwen_adapter):
        """测试：转换多条消息"""
        # Arrange
        messages = [
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.ASSISTANT, content="Hi!"),
            Message(role=MessageRole.USER, content="How are you?")
        ]

        # Act
        result = qwen_adapter._conver_message(messages)

        # Assert
        assert len(result) == 3
        assert isinstance(result[0], HumanMessage)
        assert isinstance(result[1], AIMessage)
        assert isinstance(result[2], HumanMessage)

    def test_convert_message_empty_list(self, qwen_adapter):
        """测试：转换空消息列表"""
        # Act
        result = qwen_adapter._conver_message([])

        # Assert
        assert result == []


class TestChat:
    """普通聊天功能测试"""

    def test_chat_returns_response(self, qwen_adapter):
        """测试：chat 方法返回 LLM 响应"""
        # Arrange
        messages = [Message(role=MessageRole.USER, content="Hello")]
        mock_response = MagicMock()
        mock_response.content = "Hi, how can I help you?"
        qwen_adapter._client.invoke = MagicMock(return_value=mock_response)

        # Act
        result = qwen_adapter.chat(messages)

        # Assert
        assert result == "Hi, how can I help you?"
        qwen_adapter._client.invoke.assert_called_once()

    def test_chat_with_system_prompt(self, qwen_adapter):
        """测试：带系统提示词的聊天"""
        # Arrange
        messages = [Message(role=MessageRole.USER, content="Hello")]
        system_prompt = "You are a helpful assistant"
        mock_response = MagicMock()
        mock_response.content = "Hello!"
        qwen_adapter._client.invoke = MagicMock(return_value=mock_response)

        # Act
        result = qwen_adapter.chat(messages, system_prompt=system_prompt)

        # Assert
        assert result == "Hello!"
        # 验证调用参数包含系统消息
        call_args = qwen_adapter._client.invoke.call_args[0][0]
        assert isinstance(call_args[0], SystemMessage)
        assert call_args[0].content == system_prompt

    def test_chat_empty_response(self, qwen_adapter):
        """测试：处理空响应"""
        # Arrange
        messages = [Message(role=MessageRole.USER, content="Hello")]
        mock_response = MagicMock()
        mock_response.content = ""
        qwen_adapter._client.invoke = MagicMock(return_value=mock_response)

        # Act
        result = qwen_adapter.chat(messages)

        # Assert
        assert result == ""


class TestChatStream:
    """流式聊天功能测试"""

    def test_chat_stream_yields_chunks(self, qwen_adapter):
        """测试：chat_stream 逐步返回响应"""
        # Arrange
        messages = [Message(role=MessageRole.USER, content="Hello")]
        mock_chunks = [
            MagicMock(content="Hello"),
            MagicMock(content=" there"),
            MagicMock(content="!")
        ]
        qwen_adapter._stream_client.stream = MagicMock(return_value=iter(mock_chunks))

        # Act
        result = list(qwen_adapter.chat_stream(messages))

        # Assert
        assert result == ["Hello", " there", "!"]
        qwen_adapter._stream_client.stream.assert_called_once()

    def test_chat_stream_with_system_prompt(self, qwen_adapter):
        """测试：带系统提示词的流式聊天"""
        # Arrange
        messages = [Message(role=MessageRole.USER, content="Hello")]
        system_prompt = "You are an assistant"
        mock_chunks = [MagicMock(content="Hi")]
        qwen_adapter._stream_client.stream = MagicMock(return_value=iter(mock_chunks))

        # Act
        result = list(qwen_adapter.chat_stream(messages, system_prompt=system_prompt))

        # Assert
        assert result == ["Hi"]
        # 验证调用参数包含系统消息
        call_args = qwen_adapter._stream_client.stream.call_args[0][0]
        assert isinstance(call_args[0], SystemMessage)

    def test_chat_stream_filters_empty_chunks(self, qwen_adapter):
        """测试：过滤空内容的 chunk"""
        # Arrange
        messages = [Message(role=MessageRole.USER, content="Hello")]
        mock_chunks = [
            MagicMock(content="Hello"),
            MagicMock(content=""),  # 空内容
            MagicMock(content=None),  # None 内容
            MagicMock(content=" world")
        ]
        qwen_adapter._stream_client.stream = MagicMock(return_value=iter(mock_chunks))

        # Act
        result = list(qwen_adapter.chat_stream(messages))

        # Assert
        assert result == ["Hello", " world"]

    def test_chat_stream_with_langchain_messages(self, qwen_adapter):
        """测试：使用 LangChain 消息格式的流式聊天"""
        # Arrange
        messages = [HumanMessage(content="Hello")]
        mock_chunks = [MagicMock(content="Hi")]
        qwen_adapter._stream_client.stream = MagicMock(return_value=iter(mock_chunks))

        # Act
        result = list(qwen_adapter.chat_stream(messages))

        # Assert
        assert result == ["Hi"]

    def test_chat_stream_empty_messages(self, qwen_adapter):
        """测试：处理空消息列表"""
        # Arrange
        messages = []
        mock_chunks = []
        qwen_adapter._stream_client.stream = MagicMock(return_value=iter(mock_chunks))

        # Act
        result = list(qwen_adapter.chat_stream(messages))

        # Assert
        assert result == []


class TestChatWithTools:
    """带工具调用的聊天功能测试"""

    def test_chat_with_tools_returns_response(self, qwen_adapter):
        """测试：chat_with_tools 返回 AIMessage"""
        # Arrange
        messages = [Message(role=MessageRole.USER, content="What's 2+2?")]
        tools = [MagicMock()]  # Mock tool
        mock_response = MagicMock()
        mock_llm_with_tools = MagicMock()
        mock_llm_with_tools.invoke = MagicMock(return_value=mock_response)
        qwen_adapter._client.bind_tools = MagicMock(return_value=mock_llm_with_tools)

        # Act
        result = qwen_adapter.chat_with_tools(messages, tools)

        # Assert
        assert result == mock_response
        qwen_adapter._client.bind_tools.assert_called_once_with(tools)
        mock_llm_with_tools.invoke.assert_called_once()

    def test_chat_with_tools_no_tools(self, qwen_adapter):
        """测试：没有工具时的处理"""
        # Arrange
        messages = [Message(role=MessageRole.USER, content="Hello")]
        tools = []
        mock_response = MagicMock()
        qwen_adapter._client.invoke = MagicMock(return_value=mock_response)

        # Act
        result = qwen_adapter.chat_with_tools(messages, tools)

        # Assert
        assert result == mock_response
        qwen_adapter._client.invoke.assert_called_once()

    def test_chat_with_tools_with_system_prompt(self, qwen_adapter):
        """测试：带系统提示词的工具调用"""
        # Arrange
        messages = [HumanMessage(content="Calculate 2+2")]
        system_prompt = "You are a math assistant"
        tools = [MagicMock()]
        mock_response = MagicMock()
        mock_llm_with_tools = MagicMock()
        mock_llm_with_tools.invoke = MagicMock(return_value=mock_response)
        qwen_adapter._client.bind_tools = MagicMock(return_value=mock_llm_with_tools)

        # Act
        result = qwen_adapter.chat_with_tools(messages, tools, system_prompt=system_prompt)

        # Assert
        assert result == mock_response
        # 验证消息列表包含系统提示
        call_args = mock_llm_with_tools.invoke.call_args[0][0]
        assert isinstance(call_args[0], SystemMessage)
        assert call_args[0].content == system_prompt

    def test_chat_with_tools_none_tools(self, qwen_adapter):
        """测试：工具参数为 None 时的处理"""
        # Arrange
        messages = [Message(role=MessageRole.USER, content="Hello")]
        tools = None
        mock_response = MagicMock()
        qwen_adapter._client.invoke = MagicMock(return_value=mock_response)

        # Act
        result = qwen_adapter.chat_with_tools(messages, tools)

        # Assert
        assert result == mock_response


class TestQwenAdapterIntegration:
    """QwenAdapter 集成测试"""

    def test_full_conversation_flow(self, qwen_adapter):
        """测试：完整对话流程"""
        # Arrange
        messages = [
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.ASSISTANT, content="Hi there!"),
            Message(role=MessageRole.USER, content="How are you?")
        ]
        mock_response = MagicMock()
        mock_response.content = "I'm doing well, thank you!"
        qwen_adapter._client.invoke = MagicMock(return_value=mock_response)

        # Act
        result = qwen_adapter.chat(messages)

        # Assert
        assert result == "I'm doing well, thank you!"
        # 验证消息转换正确
        call_args = qwen_adapter._client.invoke.call_args[0][0]
        assert len(call_args) == 3
