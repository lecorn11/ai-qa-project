"""UserService 单元测试"""
import pytest
from unittest.mock import MagicMock, patch

from ai_qa.application.user_service import UserService
from ai_qa.domain.exceptions import ConflictException, ForbiddenException, UnauthorizedException


class TestUserServiceRegister:
    """注册功能测试"""

    def test_register_success(self, mock_db):
        """测试：正常注册成功"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None  # 用户不存在
        service = UserService(mock_db)

        # Act
        with patch('ai_qa.infrastructure.auth.hash_password', return_value="hashed_pwd"):
            user = service.resigter("testuser", "password123", "test@example.com")
        
        # Assert
        mock_db.add.assert_called_once()     # 验证调用了 add
        mock_db.commit.assert_called_once()  # 验证调用了 commit
    
    def test_register_duplicate_username_raisers_conflict(self, mock_db):
        """测试：用户名重复应抛出 ConflictException"""
        # Arrange 模拟用户已存在
        existing_user = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        service = UserService(mock_db)

        # Act
        with pytest.raises(ConflictException) as exc_info:
            service.resigter("existing_user", "password123")

        # Assert
        assert "用户名已存在" in str(exc_info.value)

class TestUserServiceLogin:
    """登录功能测试"""

    def test_login_success(self, mock_db):
        """测试：正常登录成功"""
        # Arrange：模拟已存在的用户
        mock_user = MagicMock()
        mock_user.status = 1
        mock_user.password_hash = "hashed_password"
        mock_user.id = "user_123"
        mock_user.username = "testuser"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        service = UserService(mock_db)
        
        # Act
        with patch('ai_qa.application.user_service.verify_password', return_value=True):
            with patch('ai_qa.application.user_service.create_access_token', return_value="fake_token"):
                user, token = service.login("testuser", "password123")
        
        # Assert
        assert user == mock_user
        assert token == "fake_token"

    def test_login_user_not_found_raises_unauthorized(self, mock_db):
        """测试：用户不存在应抛出 UnauthorizedException"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        service = UserService(mock_db)
        
        # Act & Assert
        with pytest.raises(UnauthorizedException) as exc_info:
            service.login("nonexistent", "password")
        
        assert "用户名或密码错误" in str(exc_info.value)

    def test_login_wrong_password_raises_unauthorized(self, mock_db):
        """测试：密码错误应抛出 UnauthorizedException"""
        # Arrange
        mock_user = MagicMock()
        mock_user.password_hash = "hashed_password"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        service = UserService(mock_db)
        
        # Act & Assert
        with patch('ai_qa.application.user_service.verify_password', return_value=False):
            with pytest.raises(UnauthorizedException):
                service.login("testuser", "wrong_password")

    def test_login_disabled_user_raises_forbidden(self, mock_db):
        """测试：账号被禁用应抛出 ForbiddenException"""
        # Arrange
        mock_user = MagicMock()
        mock_user.status = 0  # 禁用状态
        mock_user.password_hash = "hashed_password"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        service = UserService(mock_db)
        
        # Act & Assert
        with patch('ai_qa.application.user_service.verify_password', return_value=True):
            with pytest.raises(ForbiddenException):
                service.login("testuser", "password")
    