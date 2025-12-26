"""ID 生成工具"""
from uuid_extensions import uuid7 as uuid7_func

def generate_id() -> str:
    """
    生成有序的 UUID v7
    
    UUID v7 特点：
    - 前 48 位是毫秒级时间戳，保证有序性
    - 后面是随机数，保证唯一性
    - 格式：018f6b1c-8a3e-7xxx-xxxx-xxxxxxxxxxxx
    
    Returns:
        str: UUID v7 字符串（带连字符，36字符）
    """
    return str(uuid7_func())