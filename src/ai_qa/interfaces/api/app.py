from fastapi import FastAPI
from ai_qa.interfaces.api.routes import router

# 创建 FasrAPI 应用
app = FastAPI(
    title="AI 智能问答系统",
    description="基于 LangChain 的智能问答 API",
    version="0.1.0"
)

# 注册路由
app.include_router(router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}