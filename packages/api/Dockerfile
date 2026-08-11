# Xjoy API Backend — Docker 部署
# 构建: docker build -f packages/api/Dockerfile -t xjoy-api .
# 运行: docker run -p 8000:8000 -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY xjoy-api

FROM python:3.12-slim

WORKDIR /app

# 安装依赖
COPY packages/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY packages/api/xjoy/ ./xjoy/

# 复制数据库文件
COPY packages/db/data/ ./db/data/

# 暴露端口
EXPOSE 8000

# 设置环境变量默认值
ENV KJV_DB_PATH=/app/db/data/kjv.db
ENV USER_DB_PATH=/app/db/data/user_data.db
ENV HOST=0.0.0.0
ENV PORT=8000

# 启动服务
CMD ["sh", "-c", "uvicorn xjoy.api:app --host $HOST --port $PORT"]
