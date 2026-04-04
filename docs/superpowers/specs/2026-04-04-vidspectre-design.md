---
name: VidSpectre Design
description: 影视订阅爬取应用设计方案
type: project
---

# VidSpectre - 影视订阅爬取应用

## 1. Project Overview

- **Project Name**: VidSpectre
- **Type**: Python Web Application
- **Core Functionality**: 爬取用户订阅的电影/电视剧更新，并通过插件式通知系统推送给用户
- **Target Users**: 影视爱好者，需要跟踪影视资源更新

## 2. 技术栈

- **Backend**: Python 3.x + Flask
- **Database**: SQLite
- **Scheduler**: APScheduler
- **Frontend**: Bootstrap 5 + Vanilla JS

## 3. 架构设计

### 3.1 整体架构

采用插件式架构，核心系统与具体实现解耦：

- **Core API**: RESTful API，管理订阅、触发爬取
- **Web UI**: 订阅管理界面
- **Scheduler**: 定时任务调度
- **Plugin System**: 动态加载数据源和通知插件

### 3.2 插件接口

**DataSourcePlugin (数据源插件):**
- `name` - 插件名称
- `supported_media_types` - 支持的媒体类型
- `search(keyword)` - 搜索影视
- `get_updates(media_id)` - 获取更新信息
- `get_download_links(media_id)` - 获取下载链接

**NotifierPlugin (通知插件):**
- `name` - 插件名称
- `send(title, message, **kwargs)` - 发送通知

## 4. 目录结构

```
vid spectre/
├── app/
│   ├── __init__.py
│   ├── api/
│   ├── web/
│   ├── core/
│   ├── scheduler/
│   └── database/
├── plugins/
│   ├── loader.py
│   ├── registry.py
│   ├── interfaces.py
│   └── sources/
│       └── btbtla/
├── storage/
├── static/
├── templates/
├── config.py
├── requirements.txt
└── run.py
```

## 5. 核心功能

1. **订阅管理**: 添加/删除电影/电视剧订阅
2. **数据源插件**: btbtla.com 爬取实现
3. **定时检查**: 自动检查订阅更新
4. **通知推送**: 预留插件接口
5. **Web管理界面**: 订阅列表、搜索添加

## 6. 待定

- 通知插件的具体实现