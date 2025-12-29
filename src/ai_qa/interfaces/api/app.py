from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from ai_qa.config.settings import settings
from ai_qa.config.logging import setup_logging
from ai_qa.interfaces.api.exceptions import register_exception_handlers
from ai_qa.interfaces.api.middleware import logging_middleware
from ai_qa.interfaces.api.routes import router
from ai_qa.interfaces.api.knowledge_routes import router as knowledge_router
from ai_qa.interfaces.api.auth_routes import router as auth_router

# 配置日志
setup_logging(debug=settings.debug)

# 定义 API 标签的描述
tags_metadata = [
    {
        "name": "认证",
        "description": "用户注册、登录、获取当前用户信息。所有需要认证的接口都需要在请求头中携带 `Authorization: Bearer {token}`",
    },
    {
        "name": "对话",
        "description": "会话管理和消息发送。支持普通对话和基于知识库的 RAG 问答，支持流式响应（SSE）",
    },
    {
        "name": "知识库",
        "description": "知识库的创建、管理和文档上传。支持 PDF 和 TXT 文件，上传后自动切分并向量化存储",
    },
]

# 创建 FasrAPI 应用
app = FastAPI(
    title="AI 智能问答系统",
    description="""
## 简介

基于 **LangChain + FastAPI** 构建的智能问答 API，采用 Clean Architecture 架构设计。

### ✨ 功能特性

- 🤖 **智能对话**：接入通义千问大模型，支持多轮对话与上下文记忆
- 📚 **RAG 知识库**：上传文档构建知识库，基于文档内容精准回答
- 🔐 **用户认证**：JWT Token 认证，支持多用户隔离
- ⚡ **流式响应**：支持 Server-Sent Events (SSE) 实时返回

### 🚀 快速开始

1. 调用 `POST /api/v1/auth/register` 注册账号
2. 调用 `POST /api/v1/auth/login` 获取 Token
3. 在请求头添加 `Authorization: Bearer {token}`
4. 调用 `POST /api/v1/conversations` 创建会话
5. 调用 `POST /api/v1/conversations/{session_id}/messages/stream` 开始对话

### 📖 错误码说明

| 状态码 | 说明 |
|-------|------|
| 400 | 请求参数错误 |
| 401 | 未认证或 Token 无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 资源冲突（如用户名已存在） |
| 500 | 服务器内部错误 |
    """,
    version="0.2.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)
# 注册统一异常处理器
register_exception_handlers(app)
# 注册中间件
app.middleware("http")(logging_middleware)

# 注册 API 路由
app.include_router(router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1", tags=["知识库"])
app.include_router(auth_router, prefix="/api/v1", tags=["认证"])

# 静态文件目录
STATIC_DIR = Path(__file__).parent.parent / "web" / "static"

# 挂载静态文件
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/",include_in_schema=False)
async def root():
    """返回前端页面"""
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}