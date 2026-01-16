from datetime import datetime,timezone
import logging

from sqlalchemy.orm import Session
from ai_qa.infrastructure.database.models import User, UserMcpServer
from ai_qa.infrastructure.mcp.client import MCPClientService



logger = logging.getLogger(__name__)

class McpSettingsService:
    """MCP 设置服务"""

    def __init__(self, db: Session, mcp_client: MCPClientService) -> None:
        self._db = db
        self._mcp_client = mcp_client

    def get_available_servers(self) -> list[dict]:
        """获取可用的 MCP Server 列表（从配置文件）
        
        Returns:
            Server 信息列表，包含 name 和 description
        """
        server_names = self._mcp_client.list_available_servers()

        return [
            {"name": name, "description": None}
            for name in server_names
        ]
    
    def get_user_settings(self, user_id: str) -> dict:
        """获取用户的 MCP 设置
        
        Args:
            user_id: 用户 ID
        
        Returns:
            包含 mcp_enabled 和 servers 列表
        """

        # 获取用户的 MCP 总开关
        user = self._db.query(User).filter(User.id == user_id).first()
        mcp_enabled = user.mcp_enabled if user and hasattr(user, 'mcp_enabled') else False

        # 获取用户启用的 MCP 服务列表
        user_servers = self._db.query(UserMcpServer).filter(
            UserMcpServer.user_id == user_id,
            UserMcpServer.status == 1
        ).all()
        servers = [s.server_name for s in user_servers]

        return{
            "mcp_enabled": mcp_enabled,
            "servers": servers,
        }
    
    def update_user_settings(self, user_id: str, mcp_enabled: bool, servers: list[str]) -> dict:
        """更新用户的 MCP 设置（全量更新）
        
        Args:
            user_id: 用户 ID
            mcp_enabled: MCP 总开关
            servers: 要启用的 Server 名称列表
        
        Returns:
            更新后的设置
        """
        logger.info(f"更新 MCP 设置 user_id={user_id} mcp_enabled={mcp_enabled} servers={servers}")

        # 更新用户 MCP 总开关
        user = self._db.query(User).filter(User.id == user_id).first()
        if user:
            user.mcp_enabled = mcp_enabled
        
        # 获取可用的 Server 列表, 过滤掉无效的
        available = set(self._mcp_client.list_available_servers())
        valid_servers = [s for s in servers if s in available]

        if len(valid_servers) != len(servers):
            invalid = set(servers) - set(valid_servers)
            logger.warning(f"忽略无效的 Server: {invalid}")
        
        # 全量更新用户的 Server 选择
        # 先关闭该用户的所以 MCP 工具
        user_servers = self._db.query(UserMcpServer).filter(
            UserMcpServer.user_id == user_id,
        )
        user_servers.update({
            "status": -1,
            "updated_at": datetime.now(timezone.utc)
        })

        # 再启用选择的 Server
        for server_name in valid_servers:
            existing = self._db.query(UserMcpServer).filter(
                UserMcpServer.user_id == user_id,
                UserMcpServer.server_name == server_name
            ).first()

            if existing:
                # 已存在，更新状态
                existing.status = 1
                existing.updated_at = datetime.now(timezone.utc)
            else:
                # 不存在，新建
                new_record = UserMcpServer(
                    user_id=user_id ,
                    server_name=server_name,
                    status=1
                )
                self._db.add(new_record)
        
        self._db.commit()

        logger.info(f"MCP 设置更新完成 user_id = {user_id}")

        return{
            "mcp_enabled": mcp_enabled,
            "servers": valid_servers
        }



