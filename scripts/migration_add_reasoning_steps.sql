-- 为 Message 表添加 reasoning_steps 字段
-- 用于存储 Agent 推理过程（思考 + 工具调用）

ALTER TABLE messages 
ADD COLUMN reasoning_steps JSONB DEFAULT NULL;

-- 添加注释说明
COMMENT ON COLUMN messages.reasoning_steps IS 'Agent 推理过程，JSON 数组格式，包含 thinking, tool_start, tool_result 步骤';

-- 创建索引（可选，如果需要查询推理过程）
-- CREATE INDEX idx_messages_reasoning_steps ON messages USING GIN (reasoning_steps);
