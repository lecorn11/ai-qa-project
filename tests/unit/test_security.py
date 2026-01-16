"""Security 模块单元测试"""
import pytest
from datetime import timedelta, datetime
from unittest.mock import patch
from jose import jwt

from ai_qa.infrastructure.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    SECRET_KEY,
    ALGORITHM,
)


class TestPasswordHashing:
    """密码哈希功能测试"""

    def test_hash_password_returns_string(self):
        """测试：hash_password 返回字符串"""
        # Act
        hashed = hash_password("my_password123")

        # Assert
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_different_for_same_input(self):
        """测试：相同密码每次生成不同的哈希值（因为有盐）"""
        # Act
        hash1 = hash_password("same_password")
        hash2 = hash_password("same_password")

        # Assert
        assert hash1 != hash2  # 由于盐值不同，哈希应该不同

    def test_hash_password_empty_string(self):
        """测试：空字符串密码仍然可以哈希"""
        # Act
        hashed = hash_password("")

        # Assert
        assert isinstance(hashed, str)
        assert len(hashed) > 0


class TestPasswordVerification:
    """密码验证功能测试"""

    def test_verify_password_correct_password_returns_true(self):
        """测试：正确的密码验证通过"""
        # Arrange
        plain_password = "my_secure_password"
        hashed_password = hash_password(plain_password)

        # Act
        result = verify_password(plain_password, hashed_password)

        # Assert
        assert result is True

    def test_verify_password_wrong_password_returns_false(self):
        """测试：错误的密码验证失败"""
        # Arrange
        hashed_password = hash_password("correct_password")

        # Act
        result = verify_password("wrong_password", hashed_password)

        # Assert
        assert result is False

    def test_verify_password_empty_password_returns_false(self):
        """测试：空密码验证失败"""
        # Arrange
        hashed_password = hash_password("correct_password")

        # Act
        result = verify_password("", hashed_password)

        # Assert
        assert result is False

    def test_verify_password_case_sensitive(self):
        """测试：密码大小写敏感"""
        # Arrange
        hashed_password = hash_password("Password123")

        # Act
        result = verify_password("password123", hashed_password)

        # Assert
        assert result is False


class TestCreateAccessToken:
    """JWT Token 创建功能测试"""

    def test_create_access_token_returns_string(self):
        """测试：create_access_token 返回字符串"""
        # Act
        token = create_access_token({"sub": "user123"})

        # Assert
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_contains_payload_data(self):
        """测试：生成的 Token 包含 payload 数据"""
        # Arrange
        data = {"sub": "user123", "username": "testuser"}

        # Act
        token = create_access_token(data)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Assert
        assert decoded["sub"] == "user123"
        assert decoded["username"] == "testuser"
        assert "exp" in decoded  # 应该包含过期时间

    def test_create_access_token_with_custom_expiration(self):
        """测试：使用自定义过期时间创建 Token"""
        # Arrange
        data = {"sub": "user123"}
        expires_delta = timedelta(minutes=30)

        # Act
        token = create_access_token(data, expires_delta=expires_delta)

        # 不验证过期时间地解码 Token
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})

        # Assert
        assert "exp" in decoded
        assert decoded["sub"] == "user123"

        # 验证过期时间是在未来（大于当前时间）
        now_timestamp = datetime.utcnow().timestamp()
        exp_timestamp = decoded["exp"]
        assert exp_timestamp > now_timestamp, "Token 的过期时间应该在未来"

    def test_create_access_token_with_default_expiration(self):
        """测试：使用默认过期时间（24小时）创建 Token"""
        # Arrange
        data = {"sub": "user123"}

        # Act
        token = create_access_token(data)

        # 不验证过期时间地解码 Token
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})

        # Assert
        assert "exp" in decoded
        assert decoded["sub"] == "user123"

        # 验证过期时间是在未来（大于当前时间）
        now_timestamp = datetime.utcnow().timestamp()
        exp_timestamp = decoded["exp"]
        assert exp_timestamp > now_timestamp, "Token 的过期时间应该在未来"

    def test_create_access_token_does_not_modify_original_data(self):
        """测试：创建 Token 不修改原始数据字典"""
        # Arrange
        data = {"sub": "user123"}
        original_keys = set(data.keys())

        # Act
        create_access_token(data)

        # Assert
        assert set(data.keys()) == original_keys
        assert "exp" not in data  # 原始字典不应该被添加 exp 字段


class TestVerifyToken:
    """JWT Token 验证功能测试"""

    def test_verify_token_valid_token_returns_payload(self):
        """测试：有效的 Token 返回 payload"""
        # Arrange
        data = {"sub": "user123", "username": "testuser"}
        token = create_access_token(data)

        # Act
        payload = verify_token(token)

        # Assert
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"

    def test_verify_token_invalid_token_returns_none(self):
        """测试：无效的 Token 返回 None"""
        # Act
        payload = verify_token("invalid_token_string")

        # Assert
        assert payload is None

    def test_verify_token_expired_token_returns_none(self):
        """测试：过期的 Token 返回 None"""
        # Arrange
        data = {"sub": "user123"}
        with patch('ai_qa.infrastructure.auth.security.datetime') as mock_datetime:
            # 创建一个已经过期的 Token（过期时间设为过去）
            mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 12, 0, 0)
            token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        # Act
        payload = verify_token(token)

        # Assert
        assert payload is None

    def test_verify_token_tampered_token_returns_none(self):
        """测试：被篡改的 Token 返回 None"""
        # Arrange
        data = {"sub": "user123"}
        token = create_access_token(data)

        # 篡改 Token（修改最后几个字符）
        tampered_token = token[:-10] + "tampered!!"

        # Act
        payload = verify_token(tampered_token)

        # Assert
        assert payload is None

    def test_verify_token_empty_string_returns_none(self):
        """测试：空字符串返回 None"""
        # Act
        payload = verify_token("")

        # Assert
        assert payload is None

    def test_verify_token_with_wrong_secret_returns_none(self):
        """测试：使用错误的密钥签名的 Token 验证失败"""
        # Arrange
        wrong_secret = "wrong_secret_key_12345"
        data = {"sub": "user123"}

        # 使用错误的密钥创建 Token
        token = jwt.encode(data, wrong_secret, algorithm=ALGORITHM)

        # Act
        payload = verify_token(token)

        # Assert
        assert payload is None


class TestSecurityIntegration:
    """安全模块集成测试"""

    def test_full_authentication_flow(self):
        """测试：完整的认证流程（注册 -> 登录 -> Token 验证）"""
        # 1. 模拟注册：哈希密码
        plain_password = "user_password_123"
        hashed_password = hash_password(plain_password)

        # 2. 模拟登录：验证密码
        is_valid = verify_password(plain_password, hashed_password)
        assert is_valid is True

        # 3. 登录成功后生成 Token
        token = create_access_token({"sub": "user_id_123", "username": "testuser"})

        # 4. 后续请求验证 Token
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user_id_123"
        assert payload["username"] == "testuser"

    def test_failed_authentication_flow(self):
        """测试：失败的认证流程（错误密码）"""
        # 1. 模拟注册：哈希密码
        hashed_password = hash_password("correct_password")

        # 2. 模拟登录：使用错误密码
        is_valid = verify_password("wrong_password", hashed_password)
        assert is_valid is False

        # 3. 验证失败，不应该生成 Token（实际应用中会抛出异常）
        # 这里仅测试密码验证失败的情况
