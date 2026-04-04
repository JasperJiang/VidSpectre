# VidSpectre

影视订阅爬取应用，支持插件式数据源和 Web 管理界面。

## 功能特点

- **插件式数据源**：支持多个影视资源站，目前实现 btbtla.com
- **Web 管理界面**：订阅列表、添加/删除、搜索
- **集数追踪**：标记当前看到第几集
- **关键字过滤**：按资源质量筛选（2160p、HDR、杜比等）
- **定时检查**：按全局周期自动检测所有订阅更新
- **手动触发**：可随时手动触发爬取
- **磁力链接获取**：一键获取下载链接

## 技术栈

- Python 3.x + Flask + SQLite + SQLAlchemy
- APScheduler（定时任务）
- Tailwind CSS v3 + Vanilla JS（前端，移动端优先）

## 快速开始

### 安装依赖

```bash
cd /Users/jasper/Documents/Code/VidSpectre
uv sync
```

### 启动服务

```bash
uv run python run.py              # 默认端口 5002
uv run python run.py --port 5003 # 指定端口
```

访问 http://localhost:5002

### Docker 部署

```bash
# 构建并运行
docker build -t vidspectre .
docker run -d -p 5002:5002 -v ./storage:/app/storage --name vidspectre vidspectre

# 或使用 docker-compose
docker-compose up --build
```

## 使用说明

### 添加订阅

1. 点击「添加订阅」
2. 选择类型（电影/电视剧）
3. 输入名称搜索，选择正确的结果
4. 保存

### 展开剧集

1. 点击订阅行的「展开」按钮
2. 查看该剧集的所有资源
3. 点击资源标题获取磁力链接

### 关键字过滤

在「关键字」列输入质量要求，多个关键字用逗号分隔。

例如：`2160p,HDR` 只显示同时满足两者的资源。

### 设置爬取周期

在「设置」页面可配置全局爬取周期和失败重试次数。也支持随时「手动触发」爬取所有订阅。

## 项目结构

```
VidSpectre/
├── app/                    # Flask 应用
│   ├── api/               # REST API
│   ├── web/               # Web 界面
│   ├── core/             # 核心逻辑
│   ├── scheduler/        # 定时任务
│   └── database/         # 数据库模型
├── plugins/               # 插件系统
│   └── sources/btbtla/   # btbtla 数据源
├── templates/             # HTML 模板
├── storage/               # SQLite 数据库（gitignored）
├── Dockerfile             # Docker 镜像定义
├── docker-compose.yml     # Docker Compose 配置
├── config.py             # 配置
└── run.py               # 启动入口
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/subscriptions` | 获取订阅列表 |
| POST | `/api/subscriptions` | 添加订阅 |
| DELETE | `/api/subscriptions/<id>` | 删除订阅 |
| PUT | `/api/subscriptions/<id>` | 更新订阅 |
| GET | `/api/subscriptions/<id>/episodes` | 获取剧集列表 |
| POST | `/api/subscriptions/<id>/fetch` | 立即爬取单个订阅 |
| POST | `/api/fetch-all` | 触发所有订阅爬取（返回 task_id） |
| GET | `/api/fetch-all/<task_id>` | 轮询爬取任务状态 |
| GET | `/api/download-link` | 获取磁力链接 |
| GET | `/api/search` | 搜索媒体 |

## 注意事项

- 默认端口为 5002（避免与 AirPlay 冲突）
- `media_id` 必须正确设置，否则无法展开剧集
- 使用 `uv` 管理 Python 依赖
- 所有订阅使用统一的爬取周期，在「设置」页面配置
- Docker 部署时需挂载 `./storage:/app/storage` 以持久化数据
