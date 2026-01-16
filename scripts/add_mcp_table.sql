-- MCP 功能数据库变更
-- 执行时间：2025-01-14

-- 1. 用户表新增 MCP 总开关字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS mcp_enabled BOOLEAN DEFAULT FALSE;

-- 2. 用户 MCP 选择表
CREATE TABLE IF NOT EXISTS user_mcp_servers (
    id           VARCHAR(36) PRIMARY KEY,
    user_id      VARCHAR(36) NOT NULL REFERENCES users(id),
    server_name  VARCHAR(100) NOT NULL,
    status       SMALLINT DEFAULT 1,      -- 1=启用, 0=禁用
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 联合唯一约束：同一用户对同一 Server 只能有一条记录
    CONSTRAINT uk_user_server UNIQUE (user_id, server_name)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_user_mcp_servers_user_id ON user_mcp_servers(user_id);

-- 注释
COMMENT ON TABLE user_mcp_servers IS '用户 MCP Server 选择表';
COMMENT ON COLUMN user_mcp_servers.server_name IS '对应 mcp_servers.json 配置文件中的 key';
COMMENT ON COLUMN user_mcp_servers.status IS '1=启用, 0=禁用（软删除）';
COMMENT ON COLUMN users.mcp_enabled IS 'MCP 功能总开关';