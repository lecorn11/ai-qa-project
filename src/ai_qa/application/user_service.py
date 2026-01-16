import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from ai_qa.domain.exceptions import ConflictException, ForbiddenException, UnauthorizedException
from ai_qa.infrastructure.database.models import User
from ai_qa.infrastructure.auth import hash_password, verify_password, create_access_token

logger = logging.getLogger(__name__)

class UserService:
    """用户服务"""

    def __init__(self, db: Session):
        self._db = db

    def register(self, username: str, password: str, email: str = None) -> User:
        """用户注册"""
        logger.info(f"用户注册开始 username={username} email={email}")

        # 检查用户名是否已存在
        existing_user = self._db.query(User).filter(User.username == username).first()
        if existing_user:
            raise ConflictException("用户名已存在")
        
        # 检查邮箱是否已存在
        if email:
            existing_email = self._db.query(User).filter(User.email == email).first()
            if existing_email:
                raise ConflictException("邮箱已被注册")
        
        # 创建用户
        user = User(
            username=username,
            password_hash=hash_password(password),
            email=email,
        )

        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)

        logger.info(f"用户注册成功 user={user}")

        return user
    
    def login(self, username: str, password: str) -> tuple[User, str]:
        """ 用户登录，返回（用户，Token）"""
        logger.info(f"用户登录开始 username={username}")

        # 查找用户
        user = self._db.query(User).filter(User.username == username).first()
        if not user:
            raise UnauthorizedException("用户名或密码错误")
        
        # 验证密码
        if not verify_password(password, user.password_hash):
            raise UnauthorizedException("用户名或密码错误")
        
        # 检查账号状态(1启动，0禁用)
        if user.status != 1:
            raise ForbiddenException("账号已被禁用")
        
        # 更新最后登录时间
        user.last_login_at = datetime.now(timezone.utc)
        self._db.commit()

        # 生成 Token
        token = create_access_token({"user_id": user.id, "username": user.username})

        logger.info(f"用户登录成功 username={username}")
        return user, token
    
    def get_user_by_id(self, user_id: str) -> User | None:
        """根据 ID 获取用户"""
        return self._db.query(User).filter(User.id == user_id).first()
