"""AgentService 单元测试"""

from unittest.mock import MagicMock
from ai_qa.application.agent_service import AgentService


class TestAgentService:
    """AgentService 测试类"""

    def test_chat_return_llm_response(self, mock_llm, mock_memory):
        """测试：不使用工具时直接返回答案"""

        # Arrange 准备
        response = MagicMock()
        response.tool_calls = []
        response.content = "直接回答"

        mock_llm.chat_with_tools.return_value = response
        service = AgentService(mock_llm, mock_memory, tools=[])

        # Act 执行
        result = service.chat("test_session", "你好")

        # Assert 验证
        assert result == "直接回答"
        mock_llm.chat_with_tools.assert_called_once()

    
    def test_chat_with_tool_calls(self, mock_llm, mock_memory, mock_tool):
        """测试：需要调用工具时，执行工具并返回最终答案"""
        # Arrange
        # 第一次 LLM 调用：返回工具调用
        first_response = MagicMock()
        
        first_response.tool_calls = [
            {"name": "mock_calculator", "args": {"expression": "1+1"}, "id": "call_123"}
        ]
        first_response.content = ""
        
        # 第二次 LLM 调用：返回最终答案
        second_response = MagicMock()
        second_response.tool_calls = []  # 空，表示不需要工具了
        second_response.content = "计算结果是 42"
        
        # 设置 side_effect：按顺序返回
        mock_llm.chat_with_tools.side_effect = [first_response, second_response]
        
        # 创建 AgentService
        service = AgentService(
            llm=mock_llm,
            memory=mock_memory,
            tools=[mock_tool]
        )
        
        # Act
        result = service.chat("test_session", "计算 1+1")
        
        # Assert
        assert result == "计算结果是 42"
        assert mock_llm.chat_with_tools.call_count == 2  # LLM 被调用了两次
        mock_tool.invoke.assert_called_once()  # 工具被调用了一次

    def test_chat_saves_conversation(self, mock_llm, mock_memory):
        """测试：chat 后应保存对话历史"""
        # Arrange
        response = MagicMock()
        response.tool_calls = []
        response.content = "回复内容"

        mock_llm.chat_with_tools.return_value = response
        service = AgentService(llm=mock_llm, memory=mock_memory, tools=[])

        # Act
        service.chat("test_session", "你好")

        # Assert
        mock_memory.save_conversation.assert_called_once()

    def test_chat_max_iterations(self, mock_llm, mock_memory):
        """测试：超过最大迭代次数时返回错误提示"""
        # Arrange
        mock_tool = MagicMock()
        mock_tool.name = "infinite_tool"
        mock_tool.invoke.return_value = "result"

        # 每次都返回工具调用（模拟死循环）
        response = MagicMock()
        response.tool_calls = [
            {"name": "infinite_tool", "args": {}, "id": "call_999"}
        ]
        response.content = ""

        mock_llm.chat_with_tools.return_value = response
        service = AgentService(llm=mock_llm, memory=mock_memory, tools=[mock_tool])

        # Act
        result = service.chat("test_session", "测试")

        # Assert
        assert "简化" in result  # 包含错误提示关键词
        assert mock_llm.chat_with_tools.call_count == 10  # 达到最大迭代次数