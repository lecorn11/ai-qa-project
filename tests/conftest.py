"""pytest 共享配置和 fixtures"""
import pytest
from unittest.mock import MagicMock

from ai_qa.domain.entities import Conversation, Message, MessageRole

@pytest.fixture
def mock_llm():
    """模拟 LLM 服务"""
    llm = MagicMock()
    llm.chat.return_value = "这是 AI 的回复"
    return llm

@pytest.fixture
def mock_memory():
    """模拟对话记忆"""
    memory = MagicMock()
    memory.get_conversation.return_value= Conversation(id="test_session")
    return memory

@pytest.fixture
def mock_db():
    """模拟数据库 Session"""
    return MagicMock()

@pytest.fixture
def mock_tool():
    """模拟工具"""
    tool = MagicMock()
    tool.name = "mock_calculator"
    tool.invoke.return_value = "42"
    return tool