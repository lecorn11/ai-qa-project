import logging
import time

from fastapi import Request

logger = logging.getLogger(__name__)

async def logging_middleware(request: Request, call_text):
    """请求日志中间件"""
    start_time = time.time()

    # 处理请求
    response = await call_text(request)

    # 计算耗时
    duration = time.time() - start_time

    # 记录日志
    # # 跳过静态文件日志
    # path = request.url.path
    # if not path.startswith("/static"):
    logger.info(
        f"{request.method} {request.url.path} "
        f"status={response.status_code} "
        f"duration={duration:.3f}s"
    )
    
    return response