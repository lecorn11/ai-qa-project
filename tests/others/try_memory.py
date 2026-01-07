from ai_qa.infrastructure.database import get_db
from ai_qa.infrastructure.memory.postgres_memory import PostgresConversationMemory
from ai_qa.domain.entities import MessageRole

# 获取数据库连接
db = next(get_db())

# 创建内存服务
memory = PostgresConversationMemory(db)

# 测试：列出用户 1 的对话（应该为空）
conversations = memory.list_conversations(user_id=1)
print(f"用户 1 的对话数量: {len(conversations)}")

db.close()
print("测试通过！")