# 基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1\
    PYTHONUNBUFFERED=1

# 安装 curl（用于健康检查）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 安装项目（开发模式）
RUN pip install -e .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "run_api.py"]