"""MCP Config 模块单元测试"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from ai_qa.infrastructure.mcp.config import (
    load_mcp_config,
    get_server_names,
    _parse_server_config
)
from ai_qa.infrastructure.mcp.client import MCPServerConfig


class TestLoadMcpConfig:
    """load_mcp_config 功能测试"""

    def test_load_valid_config(self):
        """测试：加载有效的配置文件"""
        # Arrange
        config_data = {
            "mcpServers": {
                "test-server": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-test"],
                    "env": {"API_KEY": "test123"}
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Act
            result = load_mcp_config(config_path)

            # Assert
            assert len(result) == 1
            assert "test-server" in result
            config = result["test-server"]
            assert isinstance(config, MCPServerConfig)
            assert config.name == "test-server"
            assert config.command == "npx"
            assert config.args == ["-y", "@modelcontextprotocol/server-test"]
            assert config.env == {"API_KEY": "test123"}
        finally:
            Path(config_path).unlink()

    def test_load_multiple_servers(self):
        """测试：加载多个服务器配置"""
        # Arrange
        config_data = {
            "mcpServers": {
                "server1": {"command": "cmd1", "args": []},
                "server2": {"command": "cmd2", "args": ["arg1"]},
                "server3": {"command": "cmd3"}
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Act
            result = load_mcp_config(config_path)

            # Assert
            assert len(result) == 3
            assert "server1" in result
            assert "server2" in result
            assert "server3" in result
        finally:
            Path(config_path).unlink()

    def test_load_nonexistent_file_returns_empty_dict(self):
        """测试：配置文件不存在时返回空字典"""
        # Arrange
        config_path = "/nonexistent/path/config.json"

        # Act
        result = load_mcp_config(config_path)

        # Assert
        assert result == {}

    def test_load_invalid_json_raises_error(self):
        """测试：无效的 JSON 格式抛出异常"""
        # Arrange
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{invalid json content")
            config_path = f.name

        try:
            # Act & Assert
            with pytest.raises(json.JSONDecodeError):
                load_mcp_config(config_path)
        finally:
            Path(config_path).unlink()

    def test_load_missing_mcpServers_field_raises_error(self):
        """测试：缺少 mcpServers 字段抛出异常"""
        # Arrange
        config_data = {"otherField": {}}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Act & Assert
            with pytest.raises(ValueError, match="缺少 'mcpServers' 字段"):
                load_mcp_config(config_path)
        finally:
            Path(config_path).unlink()

    def test_load_mcpServers_not_dict_raises_error(self):
        """测试：mcpServers 不是字典类型抛出异常"""
        # Arrange
        config_data = {"mcpServers": ["server1", "server2"]}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Act & Assert
            with pytest.raises(ValueError, match="必须是对象类型"):
                load_mcp_config(config_path)
        finally:
            Path(config_path).unlink()

    def test_load_server_missing_command_raises_error(self):
        """测试：服务器配置缺少 command 字段抛出异常"""
        # Arrange
        config_data = {
            "mcpServers": {
                "bad-server": {
                    "args": ["test"]
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Act & Assert
            with pytest.raises(ValueError, match="缺少必填字段 'command'"):
                load_mcp_config(config_path)
        finally:
            Path(config_path).unlink()

    def test_load_with_optional_fields(self):
        """测试：包含可选字段的配置"""
        # Arrange
        config_data = {
            "mcpServers": {
                "full-server": {
                    "command": "python",
                    "args": ["server.py"],
                    "env": {"DEBUG": "true"},
                    "cwd": "/app"
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Act
            result = load_mcp_config(config_path)

            # Assert
            config = result["full-server"]
            assert config.command == "python"
            assert config.args == ["server.py"]
            assert config.env == {"DEBUG": "true"}
            assert config.cwd == "/app"
        finally:
            Path(config_path).unlink()

    def test_load_empty_mcpServers_returns_empty_dict(self):
        """测试：空的 mcpServers 返回空字典"""
        # Arrange
        config_data = {"mcpServers": {}}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Act
            result = load_mcp_config(config_path)

            # Assert
            assert result == {}
        finally:
            Path(config_path).unlink()


class TestParseServerConfig:
    """_parse_server_config 功能测试"""

    def test_parse_minimal_config(self):
        """测试：解析最小配置（只有 command）"""
        # Arrange
        name = "test-server"
        config = {"command": "test-cmd"}

        # Act
        result = _parse_server_config(name, config)

        # Assert
        assert isinstance(result, MCPServerConfig)
        assert result.name == "test-server"
        assert result.command == "test-cmd"
        assert result.args == []
        assert result.env == {}
        assert result.cwd is None

    def test_parse_full_config(self):
        """测试：解析完整配置"""
        # Arrange
        name = "full-server"
        config = {
            "command": "python",
            "args": ["server.py", "--port", "8080"],
            "env": {"API_KEY": "secret", "DEBUG": "1"},
            "cwd": "/workspace"
        }

        # Act
        result = _parse_server_config(name, config)

        # Assert
        assert result.name == "full-server"
        assert result.command == "python"
        assert result.args == ["server.py", "--port", "8080"]
        assert result.env == {"API_KEY": "secret", "DEBUG": "1"}
        assert result.cwd == "/workspace"

    def test_parse_missing_command_raises_error(self):
        """测试：缺少 command 字段抛出异常"""
        # Arrange
        name = "bad-server"
        config = {"args": ["test"]}

        # Act & Assert
        with pytest.raises(ValueError, match="缺少必填字段 'command'"):
            _parse_server_config(name, config)

    def test_parse_with_default_values(self):
        """测试：使用默认值"""
        # Arrange
        name = "default-server"
        config = {"command": "node"}

        # Act
        result = _parse_server_config(name, config)

        # Assert
        assert result.args == []
        assert result.env == {}
        assert result.cwd is None


class TestGetServerNames:
    """get_server_names 功能测试"""

    def test_get_server_names_returns_list(self):
        """测试：返回服务器名称列表"""
        # Arrange
        config_data = {
            "mcpServers": {
                "server-a": {"command": "cmd1"},
                "server-b": {"command": "cmd2"},
                "server-c": {"command": "cmd3"}
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Act
            result = get_server_names(config_path)

            # Assert
            assert isinstance(result, list)
            assert len(result) == 3
            assert "server-a" in result
            assert "server-b" in result
            assert "server-c" in result
        finally:
            Path(config_path).unlink()

    def test_get_server_names_empty_config_returns_empty_list(self):
        """测试：空配置返回空列表"""
        # Arrange
        config_data = {"mcpServers": {}}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Act
            result = get_server_names(config_path)

            # Assert
            assert result == []
        finally:
            Path(config_path).unlink()

    def test_get_server_names_nonexistent_file_returns_empty_list(self):
        """测试：文件不存在返回空列表"""
        # Arrange
        config_path = "/nonexistent/config.json"

        # Act
        result = get_server_names(config_path)

        # Assert
        assert result == []


class TestMcpConfigIntegration:
    """MCP Config 集成测试"""

    def test_full_workflow(self):
        """测试：完整的配置加载工作流"""
        # Arrange
        config_data = {
            "mcpServers": {
                "weather": {
                    "command": "python",
                    "args": ["weather_server.py"],
                    "env": {"API_KEY": "weather123"}
                },
                "database": {
                    "command": "node",
                    "args": ["db_server.js"],
                    "cwd": "/opt/db"
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Act 1: 获取服务器名称
            names = get_server_names(config_path)
            assert len(names) == 2

            # Act 2: 加载配置
            configs = load_mcp_config(config_path)
            assert len(configs) == 2

            # Act 3: 验证配置详情
            weather_config = configs["weather"]
            assert weather_config.command == "python"
            assert weather_config.env["API_KEY"] == "weather123"

            db_config = configs["database"]
            assert db_config.command == "node"
            assert db_config.cwd == "/opt/db"
        finally:
            Path(config_path).unlink()
