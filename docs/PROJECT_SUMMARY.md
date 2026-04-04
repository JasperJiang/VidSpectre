# VidSpectre 项目总结

## 项目概述

VidSpectre 是一个影视订阅爬取应用，采用插件式架构，支持：
- Web 管理界面（订阅列表、添加/删除订阅）
- 插件式数据源（目前实现 btbtla.com）
- 插件式通知系统（预留接口，暂未实现）
- 定时自动检查更新
- 集数追踪（当前看到第几集）
- 搜索关键字过滤下载资源
- 展开剧集获取磁力链接

## 技术栈

- **后端**: Python 3.x + Flask + SQLite + SQLAlchemy
- **调度**: APScheduler
- **爬虫**: requests + BeautifulSoup
- **前端**: Bootstrap 5 + Vanilla JS

## 项目结构

```
vid spectre/
├── app/
│   ├── __init__.py          # Flask应用工厂
│   ├── api/                 # REST API
│   │   ├── __init__.py      # API蓝图定义
│   │   └── routes.py
│   ├── web/                 # Web界面
│   │   ├── __init__.py      # Web蓝图定义
│   │   └── routes.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── checker.py       # 更新检查逻辑
│   ├── scheduler/
│   │   ├── __init__.py
│   │   └── tasks.py         # APScheduler任务
│   └── database/
│       ├── __init__.py
│       └── models.py        # SQLAlchemy模型
├── plugins/                 # 插件系统
│   ├── __init__.py
│   ├── interfaces.py        # 插件接口定义
│   ├── loader.py            # 插件加载器
│   ├── registry.py          # 插件注册表
│   └── sources/             # 数据源插件
│       ├── __init__.py
│       └── btbtla/
│           ├── __init__.py
│           ├── plugin.py    # 插件实现
│           └── parser.py    # 页面解析
├── templates/               # HTML模板
│   ├── base.html
│   ├── index.html
│   ├── subscription.html
│   ├── edit_subscription.html
│   └── settings.html
├── static/css/main.css
├── config.py
├── requirements.txt
└── run.py
```

## 功能迭代记录

### 1. 基础架构 (Task 1-3)
- 创建 Flask 应用、数据库模型
- 实现插件系统核心（接口、加载器、注册表）

### 2. btbtla 数据源插件 (Task 4)
- 实现搜索功能（URL: `/search/{keyword}`）
- 实现详情页解析（提取集数、资源列表）
- 资源列表直接从详情页解析，按集数分组
- 磁力链接需访问 /tdown/ 页面获取
- **Bug修复**: 搜索URL格式和CSS选择器（`.module-item`）

### 3. REST API (Task 5)
- `GET /api/subscriptions` - 列表
- `POST /api/subscriptions` - 添加
- `DELETE /api/subscriptions/<id>` - 删除
- `PUT /api/subscriptions/<id>` - 更新（含 current_episode, search_keywords）
- `GET /api/subscriptions/<id>/episodes` - 获取剧集列表（支持关键字过滤）
- `GET /api/search` - 搜索媒体
- `GET /api/plugins` - 插件列表
- `POST /api/subscriptions/<id>/fetch` - 立即爬取单个订阅
- `PUT /api/subscriptions/<id>/interval` - 更新爬取周期
- `GET /api/download-link` - 获取磁力链接

### 4. Web UI (Task 6)
- 订阅列表页面
- 添加订阅表单
- 表头：类型 | 名称 | 当前看到 | 关键字 | 最新更新 | 操作

### 5. 定时任务 (Task 7)
- APScheduler 每6小时自动检查更新
- 智能判断：只推送用户标记集数之后的更新

### 6. 集数追踪功能 (新增)
- 数据库添加 `current_episode` 字段
- 前端输入框标记当前看到第几集
- 爬取逻辑比较：用户当前集数 vs 最新集数

### 7. 剧集展开功能 (新增)
- 点击"展开"按钮展开剧集列表
- 按集数分组显示资源
- 点击资源获取磁力链接
- 未设置 media_id 的订阅显示 ⚠ 警告图标

### 8. 搜索关键字功能 (新增)
- 数据库添加 `search_keywords` 字段
- 前端在表头"关键字"列显示 **?** 帮助按钮（Bootstrap Tooltip）
- 多个关键字用逗号分隔
- 过滤逻辑：资源标题必须包含所有关键字才显示

### 9. 搜索功能Bug修复
- btbtla 搜索 URL 格式修复（`/search/{keyword}` 而非 `/search?keyword=...`）
- CSS 选择器修复（`.module-item` 匹配实际页面结构）
- 清理无法执行的死代码

### 10. 集数和爬取相关Bug修复
- **年份误识别为集数**：`parser.py` 的 `_extract_episode_number` 原来用 `(\d+)` 正则捕获数字，文件名中的 `[2023]` 年份被误认为集数。修复：优先匹配 `第(\d+)集` 格式，再从 `[...]` 括号中提取集数（1-999范围），跳过4位数以上的年份
- **最新集数排序错误**：`checker.py` 和 `api/routes.py` 中 `max(result.keys())` 使用字符串比较，导致 `"99" > "132"`（因为 `'9' > '1'`）。修复：`max(int(k) for k in result.keys())`
- **手动爬取不刷新页面**：前端 `fetchSubscription` 函数获取最新集数后不更新 DOM，修复后会自动更新"最新更新"列和已展开的剧集列表
- **重复事件绑定**：爬取按钮同时有 `onclick` 和 `addEventListener`，导致点击触发两次 API 调用，删除重复的监听器
- **代码重构**：`checker.py` 和 `api/routes.py` 中重复的爬取逻辑合并到 `_fetch_and_update_subscription` 共享函数

## 设计决策

### 为什么用 uv？
用户要求使用 uv 管理 Python 依赖，项目使用 `uv run` 执行命令。

### btbtla 插件特殊处理
- 搜索URL：`/search/{keyword}` 而非 `?keyword=`
- 下载链接不直接显示磁力，需要访问 `/tdown/` 页面获取
- 集数从下载链接标题中提取（如"第64集"）
- **重要修复**：从详情页直接解析资源列表（/detail/{id}.html），而不是访问 /tdown/

### 关键字过滤逻辑
- 用户输入：`2160p, HDR, 杜比`
- 系统过滤：资源标题包含所有关键字
- 目的：让用户筛选高质量/特定版本资源

### 表头设计
- 关键字帮助按钮放在表头，避免每个输入框重复
- 使用 Bootstrap Tooltip 展示帮助信息

### 默认端口
- 开发服务器默认端口从 5000 改为 5002（避免与 AirPlay 冲突）

## 启动方式

```bash
cd /Users/jasper/Documents/Code/VidSpectre
uv run python run.py
# 访问 http://localhost:5002 (或其他端口)
```

## API 端口问题

测试中发现 5000 端口被 AirPlay 占用，常用测试端口：5002, 5003

## 待完成功能

1. 通知推送插件（预留接口，未实现）
2. 更多的数据源插件
3. 更完善的错误处理
4. 日志系统（当前用 print）