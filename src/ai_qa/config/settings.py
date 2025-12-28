from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, model_validator

class Settings(BaseSettings):
    """ 应用配置类，自动从环境变量/.env 文件加载配置 """

    # LLM 配置
    llm_api_key: SecretStr = Field(alias="LLM_API_KEY")
    llm_base_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1", alias="LLM_BASE_URL")
    llm_model : str = Field(default="qwen-turbo", alias="LLM_MODEL_NAME")
    
    # Embedding 配置
    embedding_model_name: str = Field(default="text-embedding-v3",alias="EMBEDDING_MODEL_NAME")

    # 应用配置
    app_env: str = Field(default="development", alias="APP_ENV")
    # 日志配置
    debug: bool = Field(default= True, alias= "DEBUG")

    # 知识库持久化目录
    knowledge_persist_dir: str = Field(
        default="./data/knowledge",
        alias="KNOWLEDGE_PERSIST_DIR"
    )

    # 文件上传路径
    upload_dir: str = Field(
        default="./data/uploads",
        alias="UPLOAD_DIR"
    )

    # 数据库配置
    database_url: SecretStr = Field(
        default="postgresql://ai_qa_user:ai_qa_password@localhost:5432/ai_qa_db",
        alias="DATABASE_URL"
    )

    # JWT配置
    jwt_secret_key: SecretStr = Field(alias="JWT_SECRET_KEY")

    # Pydantic V2 配置
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        populate_by_name = True,  # 允许通过字段名或别名填充
        extra="ignore"  # 忽略额外的字段
    )

    # 配置验证
    @model_validator(mode='after')
    def vaildate_settings(self) -> 'Settings':
        # 生产环境必须关闭 debug
        if self.app_env == "production" and self.debug:
            raise ValueError("生产环境不允许开启 DEBUG 模式")
        
        # 生产环境必须使用安全的 JWT 密钥
        secret = self.jwt_secret_key.get_secret_value()
        if self.app_env == "production" and len(secret) < 32:
            raise ValueError("生产环境 JWT 密钥长度至少 32位")

        return self

# 创建全局配置实例
settings = Settings()