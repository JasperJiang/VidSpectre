# 统一调度 + 手动触发 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现统一调度所有订阅 + 手动触发功能，移除 per-subscription 的独立周期配置。

**Architecture:**
- 调度器按全局 cron 表达式定时执行，不再判断 per-subscription 的 interval
- 手动触发通过 POST /api/fetch-all 创建任务，前端轮询 GET /api/fetch-all/{task_id} 获取状态
- 重试逻辑在 _fetch_and_update_subscription 中实现，网络错误重试 N 次

**Tech Stack:** Flask, APScheduler, croniter, SQLite

---

## Task 1: 添加 FETCH_RETRY_COUNT 配置

**Files:**
- Modify: `config.py:1-19`

- [ ] **Step 1: 添加 FETCH_RETRY_COUNT 配置项**

```python
# 在 Config 类中添加
FETCH_RETRY_COUNT = int(os.environ.get("FETCH_RETRY_COUNT", "3"))  # 默认重试3次
```

- [ ] **Step 2: Commit**

```bash
git add config.py
git commit -m "config: add FETCH_RETRY_COUNT setting"
```

---

## Task 2: 创建任务状态管理器

**Files:**
- Create: `app/core/task_manager.py`

- [ ] **Step 1: 创建任务状态管理器**

```python
"""Task manager for tracking fetch-all task status"""
import uuid
from datetime import datetime
from typing import Optional

class FetchTask:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.status = "running"  # running, completed, failed
        self.total = 0
        self.completed = 0
        self.failed = 0
        self.started_at = datetime.utcnow()
        self.finished_at: Optional[datetime] = None
        self.results = []  # list of {subscription_id, name, status, latest_episode, error}

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "status": self.status,
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "results": self.results
        }

class TaskManager:
    _tasks: dict[str, FetchTask] = {}

    @classmethod
    def create_task(cls) -> str:
        task_id = datetime.utcnow().strftime("%Y%m%d-") + uuid.uuid4().hex[:8]
        cls._tasks[task_id] = FetchTask(task_id)
        return task_id

    @classmethod
    def get_task(cls, task_id: str) -> Optional[FetchTask]:
        return cls._tasks.get(task_id)

    @classmethod
    def delete_task(cls, task_id: str):
        if task_id in cls._tasks:
            del cls._tasks[task_id]
```

- [ ] **Step 2: Commit**

```bash
git add app/core/task_manager.py
git commit -m "feat: add task manager for fetch-all tracking"
```

---

## Task 3: 添加重试逻辑到 checker.py

**Files:**
- Modify: `app/core/checker.py:89-116`

- [ ] **Step 1: 修改 _fetch_and_update_subscription 添加重试逻辑**

```python
from config import Config
import time

def _fetch_and_update_subscription(subscription: Subscription, retry_count: int = None) -> tuple[bool, int | None]:
    """
    抓取订阅的最新集数并更新数据库。
    返回 (是否更新了, 最新集数或None)

    网络错误重试 retry_count 次，业务错误直接跳过。
    """
    if retry_count is None:
        retry_count = Config.FETCH_RETRY_COUNT

    plugin = registry.get_data_source(subscription.source_plugin)
    if not plugin:
        return False, None

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        for attempt in range(retry_count + 1):
            try:
                if subscription.media_type == 'movie':
                    result = loop.run_until_complete(plugin.get_movie_links(subscription.media_id))
                else:
                    result = loop.run_until_complete(plugin.get_episode_links(subscription.media_id))

                if result and result.keys():
                    latest = max(int(k) for k in result.keys())
                    if subscription.latest_episode != str(latest):
                        subscription.latest_episode = str(latest)
                        subscription.latest_update_time = datetime.utcnow()
                        db.session.commit()
                        return True, latest
                    return False, latest
                return False, None
            except (asyncio.TimeoutError, ConnectionError, requests.exceptions.RequestException) as e:
                # 网络错误，重试
                if attempt < retry_count:
                    time.sleep(2)
                    continue
                # 最后一次也失败，抛出异常
                raise
    finally:
        loop.close()
```

注意：需要导入 `time` 模块

- [ ] **Step 2: Commit**

```bash
git add app/core/checker.py
git commit -m "feat: add retry logic to _fetch_and_update_subscription"
```

---

## Task 4: 添加 fetch-all API 端点

**Files:**
- Modify: `app/api/routes.py`

- [ ] **Step 1: 添加 fetch-all API**

在文件开头添加导入:
```python
from app.core.task_manager import TaskManager
```

在 `app/api/routes.py` 末尾添加:

```python
@api_bp.route("/fetch-all", methods=["POST"])
def trigger_fetch_all():
    """手动触发所有订阅的爬取"""
    task_id = TaskManager.create_task()
    task = TaskManager.get_task(task_id)

    from app.database.models import Subscription
    from app.core.checker import _fetch_and_update_subscription
    from config import Config

    subscriptions = Subscription.query.filter_by(status='active').all()
    task.total = len(subscriptions)

    for sub in subscriptions:
        try:
            updated, latest = _fetch_and_update_subscription(sub)
            task.results.append({
                "subscription_id": sub.id,
                "name": sub.media_name,
                "status": "success" if updated else "no_update",
                "latest_episode": str(latest) if latest else None
            })
            task.completed += 1
        except Exception as e:
            task.results.append({
                "subscription_id": sub.id,
                "name": sub.media_name,
                "status": "error",
                "error": str(e)
            })
            task.failed += 1

    task.status = "completed"
    task.finished_at = datetime.utcnow()

    return jsonify({"task_id": task_id})

@api_bp.route("/fetch-all/<task_id>", methods=["GET"])
def get_fetch_all_status(task_id):
    """获取 fetch-all 任务状态"""
    task = TaskManager.get_task(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task.to_dict())
```

- [ ] **Step 2: Commit**

```bash
git add app/api/routes.py
git commit -m "feat: add fetch-all API endpoints"
```

---

## Task 5: 改造调度器 - 移除 should_run_now

**Files:**
- Modify: `app/scheduler/tasks.py`

- [ ] **Step 1: 改造调度器**

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from croniter import croniter
from datetime import datetime
from config import Config

scheduler = BackgroundScheduler()

def setup_scheduler(app):
    """Setup scheduler - 按全局 cron 表达式执行"""
    from app.core.checker import _fetch_and_update_subscription
    from app.database.models import Subscription

    def run_all_checks():
        subscriptions = Subscription.query.filter_by(status='active').all()
        for sub in subscriptions:
            _fetch_and_update_subscription(sub)

    # 解析全局 cron 表达式
    cron_expr = Config.DEFAULT_INTERVAL_CRON
    cron_parts = cron_expr.split()
    if len(cron_parts) == 5:
        trigger = CronTrigger(
            minute=cron_parts[0],
            hour=cron_parts[1],
            day=cron_parts[2],
            month=cron_parts[3],
            day_of_week=cron_parts[4]
        )
        scheduler.add_job(
            func=lambda: with_app_context(app, run_all_checks),
            trigger=trigger,
            id="check_updates",
            name="Check subscription updates",
            replace_existing=True
        )

    if not scheduler.running:
        scheduler.start()

    return scheduler

def with_app_context(app, func):
    """Run function with app context"""
    with app.app_context():
        return func()
```

- [ ] **Step 2: Commit**

```bash
git add app/scheduler/tasks.py
git commit -m "refactor: simplify scheduler to use global cron only"
```

---

## Task 6: 移除 interval API 端点

**Files:**
- Modify: `app/api/routes.py`

- [ ] **Step 1: 移除 interval API 端点**

删除这两个函数:
- `@api_bp.route("/subscriptions/<int:sub_id>/interval", methods=["GET"])`
- `@api_bp.route("/subscriptions/<int:sub_id>/interval", methods=["PUT"])`

- [ ] **Step 2: Commit**

```bash
git add app/api/routes.py
git commit -m "refactor: remove per-subscription interval API"
```

---

## Task 7: 更新设置页面 - 添加重试次数和手动触发按钮

**Files:**
- Modify: `templates/settings.html`
- Modify: `app/web/routes.py`

- [ ] **Step 1: 更新 settings.html - 添加重试次数配置**

在 `<div class="p-6">` 中的 `<form>` 内，`default_cron` 配置之后添加:

```html
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1">失败重试次数</label>
                    <input type="number" name="fetch_retry_count"
                           class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                           value="{{ fetch_retry_count }}" min="0" max="10">
                    <p class="text-xs text-gray-500 mt-1">网络错误时的重试次数，设为 0 则不重试</p>
                </div>
```

- [ ] **Step 2: 更新保存按钮旁边添加手动触发按钮**

在保存按钮后添加:

```html
                    <button type="button" id="trigger-fetch-btn"
                            class="flex-1 bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-medium">
                        手动触发
                    </button>
```

在 `{% block scripts %}` 中添加轮询逻辑:

```javascript
document.getElementById('trigger-fetch-btn').addEventListener('click', function() {
    const btn = this;
    btn.disabled = true;
    btn.textContent = '触发中...';

    fetch('/api/fetch-all', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.task_id) {
                pollTaskStatus(data.task_id);
            }
        })
        .catch(err => {
            alert('触发失败');
            btn.disabled = false;
            btn.textContent = '手动触发';
        });
});

function pollTaskStatus(taskId) {
    const btn = document.getElementById('trigger-fetch-btn');
    const interval = setInterval(function() {
        fetch('/api/fetch-all/' + taskId)
            .then(r => r.json())
            .then(data => {
                if (data.status === 'completed') {
                    clearInterval(interval);
                    btn.disabled = false;
                    btn.textContent = '完成';
                    const success = data.completed;
                    const failed = data.failed;
                    alert('完成！成功: ' + success + '，失败: ' + failed);
                    setTimeout(function() { btn.textContent = '手动触发'; }, 2000);
                } else if (data.status === 'failed') {
                    clearInterval(interval);
                    btn.disabled = false;
                    btn.textContent = '失败';
                    setTimeout(function() { btn.textContent = '手动触发'; }, 2000);
                } else {
                    btn.textContent = '爬取中 ' + data.completed + '/' + data.total;
                }
            })
            .catch(err => {
                clearInterval(interval);
                btn.disabled = false;
                btn.textContent = '失败';
            });
    }, 1000);
}
```

- [ ] **Step 3: 更新 settings route - 处理 fetch_retry_count**

修改 `app/web/routes.py`:

```python
@web_bp.route("/settings", methods=["GET", "POST"])
def settings():
    """全局设置页面"""
    if request.method == "POST":
        default_cron = request.form.get("default_cron")
        fetch_retry_count = request.form.get("fetch_retry_count", "3")

        # 保存到数据库
        setting = Setting.query.get("default_interval_cron")
        if setting:
            setting.value = default_cron
        else:
            setting = Setting(key="default_interval_cron", value=default_cron)
            db.session.add(setting)

        retry_setting = Setting.query.get("fetch_retry_count")
        if retry_setting:
            retry_setting.value = fetch_retry_count
        else:
            retry_setting = Setting(key="fetch_retry_count", value=fetch_retry_count)
            db.session.add(retry_setting)

        db.session.commit()
        # 更新内存中的值
        Config.DEFAULT_INTERVAL_CRON = default_cron
        Config.FETCH_RETRY_COUNT = int(fetch_retry_count)
        return redirect(url_for("web.settings"))

    # 获取 fetch_retry_count
    retry_setting = Setting.query.get("fetch_retry_count")
    fetch_retry_count = retry_setting.value if retry_setting else str(Config.FETCH_RETRY_COUNT)

    return render_template("settings.html",
                           default_cron=Config.DEFAULT_INTERVAL_CRON,
                           fetch_retry_count=fetch_retry_count)
```

- [ ] **Step 4: Commit**

```bash
git add templates/settings.html app/web/routes.py
git commit -m "feat: add retry count config and manual trigger button to settings"
```

---

## Task 8: 移除 index.html 中的 interval 周期选择器

**Files:**
- Modify: `templates/index.html:113-133`

- [ ] **Step 1: 删除 interval selector HTML**

删除整个 `<!-- Interval Selector -->` 区块 (lines 113-133)

- [ ] **Step 2: Commit**

```bash
git add templates/index.html
git commit -m "refactor: remove per-subscription interval selector from index"
```

---

## Task 9: 移除 app.js 中的 interval 相关代码

**Files:**
- Modify: `static/js/app.js`

- [ ] **Step 1: 移除 interval 相关函数**

删除 `initIntervalSelectors` 函数和 `saveInterval` 函数

- [ ] **Step 2: 更新 DOMContentLoaded**

从 `document.addEventListener('DOMContentLoaded', ...)` 中移除 `initIntervalSelectors()` 调用

- [ ] **Step 3: Commit**

```bash
git add static/js/app.js
git commit -m "refactor: remove interval selector JS from app.js"
```

---

## Task 10: Playwright 测试

**Files:**
- Test: `http://localhost:5002/settings`

- [ ] **Step 1: 启动服务器**

```bash
cd /Users/jasper/Documents/Code/VidSpectre && uv run python run.py &
```

- [ ] **Step 2: 打开设置页面**

使用 Playwright 打开 http://localhost:5002/settings

- [ ] **Step 3: 测试重试次数配置**

验证页面显示"失败重试次数"输入框，默认值为3

- [ ] **Step 4: 测试手动触发按钮**

点击"手动触发"按钮，验证:
- 按钮变为"触发中..."
- 然后显示"爬取中 X/Y"
- 最后显示"完成"并有 alert 显示成功/失败数量

- [ ] **Step 5: 测试首页**

打开 http://localhost:5002/ 验证 interval 选择器已移除

- [ ] **Step 6: 停止服务器**

---

## 自检清单

- [ ] Spec 覆盖：所有设计要求都有对应实现
- [ ] 占位符扫描：无 TBD/TODO/不完整代码
- [ ] 类型一致性：函数签名、方法名在整个 plan 中一致
