"""MCP Config 模块单元测试"""

import json
import tempfile
from pathlib import Path

import pytest

from ai_qa.infrastructure.mcp.client import (
    MCPServerConfig,
    SSEServerConfig,
    StdioServerConfig,
    StreamableHTTPServerConfig,
    TransportType,
)
from ai_qa.infrastructure.mcp.config import get_server_names, load_mcp_config


class TestMCPServerConfigFromDict:
    """MCPServerConfig.from_dict 工厂方法测试"""

    def test_create_stdio_config_default_transport(self):
        """测试：不指定 transport 时默认创建 Stdio 配置"""
        # Arrange
        name = "test-server"
        data = {"command": "npx", "args": ["-y", "some-package"]}

        # Act
        config = MCPServerConfig.from_dict(name, data)

        # Assert
        assert isinstance(config, StdioServerConfig)
        assert config.name == "test-server"
        assert config.transport == TransportType.STDIO
        assert config.command == "npx"
        assert config.args == ["-y", "some-package"]

    def test_create_stdio_config_explicit_transport(self):
        """测试：显式指定 stdio transport"""
        # Arrange
        name = "stdio-server"
        data = {
            "transport": "stdio",
            "command": "python",
            "args": ["server.py"],
            "env": {"DEBUG": "true"},
            "cwd": "/app",
        }

        # Act
        config = MCPServerConfig.from_dict(name, data)

        # Assert
        assert isinstance(config, StdioServerConfig)
        assert config.transport == TransportType.STDIO
        assert config.command == "python"
        assert config.args == ["server.py"]
        assert config.env == {"DEBUG": "true"}
        assert config.cwd == "/app"

    def test_create_sse_config(self):
        """测试：创建 SSE 配置"""
        # Arrange
        name = "sse-server"
        data = {
            "transport": "sse",
            "url": "http://localhost:8000/sse",
            "headers": {"Authorization": "Bearer token123"},
            "timeout": 60.0,
        }

        # Act
        config = MCPServerConfig.from_dict(name, data)

        # Assert
        assert isinstance(config, SSEServerConfig)
        assert config.name == "sse-server"
        assert config.transport == TransportType.SSE
        assert config.url == "http://localhost:8000/sse"
        assert config.headers == {"Authorization": "Bearer token123"}
        assert config.timeout == 60.0

    def test_create_sse_config_with_defaults(self):
        """测试：SSE 配置使用默认值"""
        # Arrange
        name = "sse-minimal"
        data = {"transport": "sse", "url": "http://example.com/sse"}

        # Act
        config = MCPServerConfig.from_dict(name, data)

        # Assert
        assert isinstance(config, SSEServerConfig)
        assert config.headers == {}
        assert config.timeout == 30.0

    def test_create_streamable_http_config(self):
        """测试：创建 Streamable HTTP 配置"""
        # Arrange
        name = "http-server"
        data = {
            "transport": "streamable_http",
            "url": "http://localhost:8000/mcp",
            "headers": {"X-API-Key": "secret"},
            "timeout": 45.0,
        }

        # Act
        config = MCPServerConfig.from_dict(name, data)

        # Assert
        assert isinstance(config, StreamableHTTPServerConfig)
        assert config.name == "http-server"
        assert config.transport == TransportType.STREAMABLE_HTTP
        assert config.url == "http://localhost:8000/mcp"
        assert config.headers == {"X-API-Key": "secret"}
        assert config.timeout == 45.0

    def test_unknown_transport_raises_error(self):
        """测试：未知传输类型抛出异常"""
        # Arrange
        name = "bad-server"
        data = {"transport": "websocket", "url": "ws://localhost"}

        # Act & Assert
        with pytest.raises(ValueError, match="未知的传输类型"):
            MCPServerConfig.from_dict(name, data)

    def test_stdio_missing_command_raises_error(self):
        """测试：Stdio 配置缺少 command 抛出异常"""
        # Arrange
        name = "bad-stdio"
        data = {"transport": "stdio", "args": ["test"]}

        # Act & Assert
        with pytest.raises(ValueError, match="缺少必填字段 'command'"):
            MCPServerConfig.from_dict(name, data)

    def test_sse_missing_url_raises_error(self):
        """测试：SSE 配置缺少 url 抛出异常"""
        # Arrange
        name = "bad-sse"
        data = {"transport": "sse", "headers": {}}

        # Act & Assert
        with pytest.raises(ValueError, match="缺少必填字段 'url'"):
            MCPServerConfig.from_dict(name, data)

    def test_streamable_http_missing_url_raises_error(self):
        """测试：Streamable HTTP 配置缺少 url 抛出异常"""
        # Arrange
        name = "bad-http"
        data = {"transport": "streamable_http"}

        # Act & Assert
        with pytest.raises(ValueError, match="缺少必填字段 'url'"):
            MCPServerConfig.from_dict(name, data)


class TestLoadMcpConfig:
    """load_mcp_config 功能测试"""

    def test_load_mixed_transport_config(self):
        """测试：加载包含多种传输类型的配置文件"""
        # Arrange
        config_data = {
            "mcpServers": {
                "local-server": {
                    "transport": "stdio",
                    "command": "npx",
                    "args": ["-y", "some-package"],
                },
                "remote-sse": {
                    "transport": "sse",
                    "url": "http://localhost:8000/sse",
                },
                "remote-http": {
                    "transport": "streamable_http",
                    "url": "http://localhost:8000/mcp",
                },
            }
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Act
            result = load_mcp_config(config_path)

            # Assert
            assert len(result) == 3

            assert isinstance(result["local-server"], StdioServerConfig)
            assert result["local-server"].command == "npx"

            assert isinstance(result["remote-sse"], SSEServerConfig)
            assert result["remote-sse"].url == "http://localhost:8000/sse"

            assert isinstance(result["remote-http"], StreamableHTTPServerConfig)
            assert result["remote-http"].url == "http://localhost:8000/mcp"

        finally:
            Path(config_path).unlink()

    def test_load_default_transport_is_stdio(self):
        """测试：不指定 transport 时默认为 stdio"""
        # Arrange
        config_data = {
            "mcpServers": {
                "legacy-server": {
                    "command": "node",
                    "args": ["server.js"],
                }
            }
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Act
            result = load_mcp_config(config_path)

            # Assert
            config = result["legacy-server"]
            assert isinstance(config, StdioServerConfig)
            assert config.transport == TransportType.STDIO

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
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
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

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
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

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Act & Assert
            with pytest.raises(ValueError, match="必须是对象类型"):
                load_mcp_config(config_path)
        finally:
            Path(config_path).unlink()

    def test_load_empty_mcpServers_returns_empty_dict(self):
        """测试：空的 mcpServers 返回空字典"""
        # Arrange
        config_data = {"mcpServers": {}}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Act
            result = load_mcp_config(config_path)

            # Assert
            assert result == {}
        finally:
            Path(config_path).unlink()


class TestGetServerNames:
    """get_server_names 功能测试"""

    def test_get_server_names_returns_list(self):
        """测试：返回服务器名称列表"""
        # Arrange
        config_data = {
            "mcpServers": {
                "server-a": {"command": "cmd1"},
                "server-b": {"transport": "sse", "url": "http://example.com/sse"},
                "server-c": {"transport": "streamable_http", "url": "http://example.com/mcp"},
            }
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
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

    def test_get_server_names_nonexistent_file_returns_empty_list(self):
        """测试：配置文件不存在时返回空列表"""
        # Act
        result = get_server_names("/nonexistent/config.json")

        # Assert
        assert result == []


class TestTransportType:
    """TransportType 枚举测试"""

    def test_transport_type_values(self):
        """测试：枚举值正确"""
        assert TransportType.STDIO.value == "stdio"
        assert TransportType.SSE.value == "sse"
        assert TransportType.STREAMABLE_HTTP.value == "streamable_http"

    def test_transport_type_from_string(self):
        """测试：从字符串创建枚举"""
        assert TransportType("stdio") == TransportType.STDIO
        assert TransportType("sse") == TransportType.SSE
        assert TransportType("streamable_http") == TransportType.STREAMABLE_HTTP

    def test_transport_type_invalid_string_raises_error(self):
        """测试：无效字符串抛出异常"""
        with pytest.raises(ValueError):
            TransportType("invalid")
