from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from ai_qa.interfaces.api.routes import router
from ai_qa.interfaces.api.knowledge_routes import router as knowledge_router
from ai_qa.interfaces.api.auth_routes import router as auth_router


# 创建 FasrAPI 应用
app = FastAPI(
    title="AI 智能问答系统",
    description="基于 LangChain 的智能问答 API, 支持 RAG 知识库",
    version="0.2.0"
)

# 注册 API 路由
app.include_router(router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1", tags=["知识库"])
app.include_router(auth_router, prefix="/api/v1", tags=["认证"])

# 静态文件目录
STATIC_DIR = Path(__file__).parent.parent / "web" / "static"

# 挂载静态文件
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def root():
    """返回前端页面"""
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}