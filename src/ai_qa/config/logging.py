import logging
import sys

def setup_logging(debug: bool = False):
    """配置日志系统"""

    # 根据环境环境决定日志级别
    level = logging.DEBUG if debug else logging.INFO

    # 日志格式
    format_str = "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"

    # 配置根 logger
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler(sys.stdout) # 输出到控制台
        ]
    )

    # 降低第三方库的日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)