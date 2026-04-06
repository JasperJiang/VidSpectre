# 定时任务开关与手动执行功能设计

## 概述

为 VidSpectre 添加定时任务开关和订阅列表手动执行功能。

## 功能需求

### 1. 定时任务开关
- 在设置页面单独一行添加 Toggle 开关，控制定时任务的开启/关闭
- 开关状态保存到 `Setting` 表（key: `scheduler_enabled`，value: `"true"` 或 `"false"`）
- 默认值为 `"true"`（开启）
- 关闭时保留 cron 表达式不变
- 调度器在应该执行时检查开关状态，如果关闭则跳过

### 2. 订阅列表手动执行
- 在订阅卡片列表最上方添加"手动执行"按钮
- 点击后调用 `POST /api/fetch-all`
- 复用现有 `task_id` 轮询机制
- 执行完成后显示结果区域，3秒后自动消失，然后刷新订阅列表

### 3. 执行结果展示
- 结果区域显示在订阅列表最上方（订阅卡片区域上方）
- 成功时显示："✓ 成功 X 个"（绿色文字）
- 失败时显示："✗ 失败：订阅名称1、订阅名称2"（红色文字）
- 如果全部成功，只显示成功信息
- 3秒后自动消失
- 消失后刷新订阅列表

## 实现方案

### 数据库变更
- 新增 `Setting` 记录：`scheduler_enabled` = `"true"`（默认）

### 后端修改

#### 1. `app/__init__.py`
- 启动时加载 `scheduler_enabled` 到 `Config.SCHEDULER_ENABLED`（默认 `True`）

#### 2. `app/scheduler/tasks.py`
- 提取公共逻辑为 `_run_all_checks()` 函数（供 scheduler 和 API 共用）
- `setup_scheduler()` 中，调度器执行前检查 `Config.SCHEDULER_ENABLED`
- 如果为 `False`，跳过本次执行（但调度器本身继续运行）

#### 3. `app/web/routes.py`
- `settings` 路由处理 `scheduler_enabled` 的保存
- 如果开关关闭，值设为 `"false"`

#### 4. `app/api/routes.py`
- `POST /api/fetch-all` 调用 `_run_all_checks()` 替代重复代码
- 检查 `Config.SCHEDULER_ENABLED`，如果为 `False`，返回错误信息

#### 5. 新增函数 `app/core/checker.py`
```python
def _run_all_subscriptions():
    """遍历所有活跃订阅并执行抓取，返回 (results, failed_count)"""
    results = []
    failed_count = 0
    subscriptions = Subscription.query.filter_by(status='active').all()
    for sub in subscriptions:
        try:
            updated, latest = _fetch_and_update_subscription(sub)
            results.append({
                "subscription_id": sub.id,
                "name": sub.media_name,
                "status": "success" if updated else "no_update",
                "latest_episode": str(latest) if latest else None
            })
        except Exception as e:
            results.append({
                "subscription_id": sub.id,
                "name": sub.media_name,
                "status": "error",
                "error": str(e)
            })
            failed_count += 1
    return results, failed_count
```

- Scheduler 调用：只调用 `_run_all_subscriptions()` 不使用返回值
- API 调用：使用返回值填充 `task.results`

### 前端修改

#### 1. `templates/settings.html`
- 在 cron 表达式输入区域下方添加 Toggle 开关
- 开关旁边添加文字说明："启用定时任务"
- 开关样式与现有表单风格一致

#### 2. `templates/index.html`
- 在订阅卡片列表上方添加结果区域容器（默认隐藏）
- 添加手动执行按钮，样式与现有按钮一致
- 结果区域结构：
  ```html
  <div id="fetch-result" class="hidden mb-4 p-4 rounded-lg">
    <span id="fetch-result-text"></span>
  </div>
  ```

#### 3. `static/js/app.js`
- 添加 `triggerFetchAll()` 函数
- 轮询 task_id 状态
- 显示结果区域，3秒后隐藏并刷新订阅列表
- 添加按钮 loading 状态

## 文件修改清单

| 文件 | 修改内容 |
|------|----------|
| `app/__init__.py` | 加载 `scheduler_enabled` |
| `app/core/checker.py` | 新增 `_run_all_subscriptions()` 公共函数 |
| `app/scheduler/tasks.py` | 调用公共函数，添加开关检查 |
| `app/web/routes.py` | 处理开关保存 |
| `app/api/routes.py` | 调用公共函数，fetch-all 检查开关 |
| `config.py` | 添加 `SCHEDULER_ENABLED` 配置项 |
| `templates/settings.html` | 添加开关 UI |
| `templates/index.html` | 添加结果区域和手动执行按钮 |
| `static/js/app.js` | 添加轮询和结果显示逻辑 |

## 测试验证

1. **开关功能测试**
   - 关闭开关后，定时任务不执行
   - 重新开启后，定时任务恢复正常

2. **手动执行测试**
   - 点击手动执行按钮，按钮显示 loading 状态
   - 执行完成后显示结果（成功/失败）
   - 3秒后结果消失，订阅列表刷新

3. **失败显示测试**
   - 确保至少一个订阅 fetch 失败时，能正确显示失败列表

4. **代码复用验证**
   - Scheduler 和 API 手动触发调用同一个 `_run_all_subscriptions()` 函数

## 测试验证

1. **开关功能测试**
   - 关闭开关后，定时任务不执行
   - 重新开启后，定时任务恢复正常

2. **手动执行测试**
   - 点击手动执行按钮，按钮显示 loading 状态
   - 执行完成后显示结果（成功/失败）
   - 3秒后结果消失，订阅列表刷新

3. **失败显示测试**
   - 确保至少一个订阅 fetch 失败时，能正确显示失败列表
