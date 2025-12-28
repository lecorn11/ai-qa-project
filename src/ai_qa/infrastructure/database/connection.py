from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from ai_qa.config.settings import settings

# 创建数据库引擎
engine = create_engine(
    settings.database_url.get_secret_value(),
    pool_size=5,             # 连接池大小
    max_overflow=10,         # 超出 pool_size 后最多再创建的连接数
    pool_pre_ping=True,      # 连接前检查连接是否有效
    echo=False               # True 会打印所有 SQL，调试时可以开启
)

# 创建 Session 工厂
SessionLocal = sessionmaker(
    autocommit=False,        # 需要手动 commit，不会自动提交
    autoflush=False,         # 查询前不自动把内存变更刷到数据库
    bind=engine              # 绑定到上面创建的引擎
)

def get_db() -> Generator[Session, None, None]:
    """获取数据库会话（用于 FastAPI 依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()