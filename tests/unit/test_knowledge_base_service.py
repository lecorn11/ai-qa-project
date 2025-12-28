"""KnowledgeBaseService 单元测试"""
import pytest
from unittest.mock import MagicMock

from ai_qa.application.knowledge_base_service import KnowledgeBaseService
from ai_qa.infrastructure.database.models import KnowledgeBase as KnowledgeBaseModel


class TestKnowledgeBaseServiceCreate:
    """创建知识库测试"""

    def test_create_success(self, mock_db):
        """测试：创建知识库成功"""
        # Arrange
        service = KnowledgeBaseService(mock_db)
        
        # Act
        kb = service.create(
            user_id="user_123",
            name="测试知识库",
            description="这是描述"
        )
        
        # Assert
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()


class TestKnowledgeBaseServiceGetById:
    """获取知识库测试"""

    def test_get_by_id_found(self, mock_db):
        """测试：知识库存在时返回知识库"""
        # Arrange
        mock_kb = MagicMock(spec=KnowledgeBaseModel)
        mock_kb.id = "kb_123"
        mock_kb.name = "测试知识库"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_kb
        service = KnowledgeBaseService(mock_db)
        
        # Act
        result = service.get_by_id("kb_123", "user_123")
        
        # Assert
        assert result == mock_kb

    def test_get_by_id_not_found(self, mock_db):
        """测试：知识库不存在时返回 None"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        service = KnowledgeBaseService(mock_db)
        
        # Act
        result = service.get_by_id("nonexistent", "user_123")
        
        # Assert
        assert result is None


class TestKnowledgeBaseServiceDelete:
    """删除知识库测试"""

    def test_delete_success(self, mock_db):
        """测试：删除成功返回 True"""
        # Arrange
        mock_kb = MagicMock()
        mock_kb.status = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_kb
        service = KnowledgeBaseService(mock_db)
        
        # Act
        result = service.delete("kb_123", "user_123")
        
        # Assert
        assert result is True
        assert mock_kb.status == -1  # 验证状态改为 -1（软删除）
        mock_db.commit.assert_called_once()

    def test_delete_not_found(self, mock_db):
        """测试：知识库不存在时返回 False"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        service = KnowledgeBaseService(mock_db)
        
        # Act
        result = service.delete("nonexistent", "user_123")
        
        # Assert
        assert result is False