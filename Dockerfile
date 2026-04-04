FROM python:3.13-slim

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# 使用 uv 安装依赖
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# 复制应用代码
COPY . .

# 创建存储目录
RUN mkdir -p storage

# 声明挂载点（需在运行容器时挂载以持久化数据）
VOLUME ["/app/storage"]

# 暴露端口
EXPOSE 5002

# 使用 gunicorn 运行 (--preload 避免多 worker 竞态)
CMD ["uv", "run", "gunicorn", "-w", "4", "--preload", "-b", "0.0.0.0:5002", "run:app"]
