# 统一调度 + 手动触发 设计方案

**日期**: 2026-04-04
**状态**: 已批准

## 1. 概述

将 per-subscription 的独立爬取周期改为全局统一调度，同时支持手动触发爬取所有订阅。

## 2. 核心改动

### 2.1 调度器改造

- 移除 `should_run_now()` 判断逻辑
- 调度器按 `Config.DEFAULT_INTERVAL_CRON` 的 cron 表达式定时执行（使用 `croniter`）
- 每次触发爬取所有 active 订阅

### 2.2 全局配置（设置页面）

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `default_interval_cron` | 全局爬取周期（cron 表达式） | `0 */6 * * *` |
| `fetch_retry_count` | 失败重试次数 | 3 |

### 2.3 手动触发 API

```
POST /api/fetch-all
Response: {"task_id": "20260404-abc123"}

GET /api/fetch-all/<task_id>
Response: {
  "status": "running",  // running | completed | failed
  "total": 10,
  "completed": 3,
  "failed": 0,
  "results": [
    {"subscription_id": 1, "name": "剧A", "status": "success", "latest_episode": "12"},
    {"subscription_id": 2, "name": "剧B", "status": "retried", "error": "timeout"},
  ]
}
```

### 2.4 重试逻辑

- 网络错误（超时、5xx）→ 重试 N 次，间隔2秒
- 业务错误（media_id 不存在、解析失败）→ 直接跳过，不重试
- 每个订阅独立，不因一个失败影响其他

### 2.5 移除功能

- API 端点 `GET/PUT /subscriptions/<id>/interval` 移除
- 前端编辑订阅页面的周期配置去掉
- `Subscription.interval_cron` 字段保留（数据库层面），但代码不再读取

## 3. 前端改动

### 3.1 设置页面

- 在保存按钮旁边加"手动触发"按钮
- 点击后显示 loading → 轮询状态 → 显示结果摘要

## 4. 架构

```
手动触发 或 定时调度
       ↓
  创建 Task ID，记录到内存
       ↓
  遍历所有 active 订阅
       ↓
  对每个订阅：重试 N 次调用 _fetch_and_update_subscription
       ↓
  更新 Task 状态（progress, results）
       ↓
  前端轮询直到 completed/failed
```

## 5. 测试

使用 Playwright 测试：
- 设置页面能正确保存配置
- 手动触发按钮能正常调用 API
- 轮询能正确显示进度和结果
