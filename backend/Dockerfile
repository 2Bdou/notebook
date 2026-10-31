# 基础镜像：Python 3.12 精简版
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 先拷贝依赖文件，利用 Docker 层缓存加速构建
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝项目源码
COPY . .

# 创建数据目录（SQLite 数据库文件存放位置）
RUN mkdir -p /app/data

# 暴露服务端口
EXPOSE 8000

# 启动 FastAPI 服务（监听所有网卡，端口 8000）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
