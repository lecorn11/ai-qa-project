import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "ai_qa.interfaces.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True # 开发模式，代码修改自动重启
    )

    