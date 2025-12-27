from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from ai_qa.domain.exceptions import AppException, NotFoundException

def register_exception_handlers(app):
    app.add_exception_handler(AppException,app_exception_handler)
    app.add_exception_handler(HTTPException,http_exception_handler)
    app.add_exception_handler(Exception,global_exception_handler)

# 全局异常处理器
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail":"服务异常，请联系管理员"}
    )

# HTTP异常
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail":exc.detail}
    )

async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail":exc.detail}
    )