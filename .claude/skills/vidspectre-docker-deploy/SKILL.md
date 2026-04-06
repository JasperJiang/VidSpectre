---
name: vidspectre-docker-deploy
description: Use to rebuild and redeploy VidSpectre Docker container - includes build, cleanup, and volume mounting
---

# VidSpectre Docker 部署

## 用途

重新构建并部署 VidSpectre Docker 环境。

## 使用场景

- 代码更新后需要重新部署
- 镜像需要重建
- 容器需要重启

## 执行步骤

### 1. 清理旧容器和镜像

```bash
# 停止并删除运行中的容器
docker rm -f vidspectre

# 删除旧镜像（可选，如果需要完全重建）
docker rmi jasperjiang/vidspectre
```

### 2. 构建新镜像

```bash
docker build -t jasperjiang/vidspectre --platform linux/amd64 .
```

### 3. 运行容器（挂载 storage 卷）

```bash
docker run -d -p 5002:5002 -v $(pwd)/storage:/app/storage --name vidspectre jasperjiang/vidspectre
```

## 完整命令序列

```bash
docker rm -f vidspectre 2>/dev/null
docker rmi jasperjiang/vidspectre 2>/dev/null
docker build -t jasperjiang/vidspectre --platform linux/amd64 .
docker run -d -p 5002:5002 -v $(pwd)/storage:/app/storage --name vidspectre jasperjiang/vidspectre
sleep 5
```

## 验证

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:5002/
# 期望输出: 200
```

## 注意事项

- storage 卷必须挂载以持久化 SQLite 数据库
- 端口 5002 必须可用
- 镜像构建使用 uv sync --frozen 安装依赖
- 多平台构建需要 Docker BuildKit (buildx)
- 推送多平台镜像前需先登录 Docker Hub
