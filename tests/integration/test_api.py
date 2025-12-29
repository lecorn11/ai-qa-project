"""API 集成测试"""
from datetime import datetime
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from ai_qa.interfaces.api.app import app
from ai_qa.interfaces.api.dependecnies import get_db, get_current_user
from ai_qa.infrastructure.database.models import User


# ============ Fixtures ============

@pytest.fixture
def mock_db():
    """模拟数据库"""
    return MagicMock()


@pytest.fixture
def mock_user():
    """模拟已登录用户"""
    user = MagicMock(spec=User)
    user.id = "user_123"
    user.username = "testuser"
    user.email = "test@example.com"
    user.nickname = "t"
    user.status = 1
    return user


@pytest.fixture
def client(mock_db, mock_user):
    """创建测试客户端，覆盖依赖"""
    # 覆盖依赖
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with TestClient(app) as c:
        yield c
    
    # 清理
    app.dependency_overrides.clear()


@pytest.fixture
def client_no_auth(mock_db):
    """未登录的测试客户端"""
    app.dependency_overrides[get_db] = lambda: mock_db
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()


# ============ 健康检查测试 ============

class TestHealthCheck:
    """健康检查 API 测试"""

    def test_health_check(self, client):
        """测试：健康检查返回 ok"""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


# ============ 认证 API 测试 ============

class TestAuthAPI:
    """认证相关 API 测试"""

    def test_register_success(self, client_no_auth, mock_db):
        """测试：注册成功"""
        # Mock：用户不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None
        # 模拟 refresh：给对象设置 id 和 status
        def fake_refresh(user):
            user.id = "test-uuid-123"
            user.status = 1
    
        mock_db.refresh.side_effect = fake_refresh

        with patch('ai_qa.infrastructure.auth.hash_password', return_value="hashed"):
            response = client_no_auth.post("/api/v1/auth/register", json={
                "username": "newuser",
                "password": "password123",
                "email": "new@example.com"
            })
        
        assert response.status_code == 200
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_register_duplicate_username(self, client_no_auth, mock_db):
        """测试：用户名重复返回 409"""
        # Mock：用户已存在
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
        
        response = client_no_auth.post("/api/v1/auth/register", json={
            "username": "existing",
            "password": "password123"
        })
        
        assert response.status_code == 409

    def test_get_me_success(self, client, mock_user):
        """测试：获取当前用户信息"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == mock_user.username


# ============ 会话 API 测试 ============

class TestConversationAPI:
    """会话相关 API 测试"""

    def test_create_conversation(self, client, mock_db):
        """测试：创建新会话"""
        response = client.post("/api/v1/conversations")
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data

    def test_list_conversations(self, client, mock_db):
        """测试：获取会话列表"""
        # Mock：返回空列表
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        response = client.get("/api/v1/conversations")
        
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data


# ============ 知识库 API 测试 ============

class TestKnowledgeBaseAPI:
    """知识库相关 API 测试"""

    def test_create_knowledge_base(self, client, mock_db):
        """测试：创建知识库"""
        # 模拟 refresh：给对象设置 id 和时间
        def fake_refresh(kb):
            kb.id = "test-uuid-123"
            kb.created_at = datetime.now()
            kb.updated_at = datetime.now()
    
        mock_db.refresh.side_effect = fake_refresh

        response = client.post("/api/v1/knowledge-bases", json={
            "name": "测试知识库",
            "description": "这是描述"
        })
        
        assert response.status_code == 200
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_list_knowledge_bases(self, client, mock_db):
        """测试：获取知识库列表"""
        # Mock：返回空列表
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        response = client.get("/api/v1/knowledge-bases")
        
        assert response.status_code == 200
        data = response.json()
        assert "knowledge_bases" in data