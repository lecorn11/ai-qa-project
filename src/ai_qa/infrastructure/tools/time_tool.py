from datetime import datetime
from langchain_core.tools import tool

@tool
def get_current_time() -> str:
    """
    获取当前的日期和时间

    返回格式：YYYY-MM-DD HH:MM:SS （如 2025-12-30 21:30:00）
    当用户询问“今天几号“、“现在几点“、“当前时间“等问题时使用此工具。
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")