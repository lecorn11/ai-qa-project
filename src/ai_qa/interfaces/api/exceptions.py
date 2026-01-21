import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from ai_qa.domain.exceptions import AppException

logger = logging.getLogger(__name__)

def register_exception_handlers(app):
    app.add_exception_handler(AppException,app_exception_handler)
    app.add_exception_handler(Exception,global_exception_handler)

# 全局异常处理器
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"请求处理失败 url={request.url}，方法{request.method}")
    return JSONResponse(
        status_code=500,
        content={"detail":"服务异常，请联系管理员"}
    )

async def app_exception_handler(request: Request, exc: AppException):
    logger.warning(f"业务异常 url={request.url} status={exc.status_code} detail={exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail":exc.detail}
    )