# Scheduler Toggle and Manual Fetch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 添加定时任务开关和订阅列表手动执行功能

**Architecture:** 提取公共函数 `_run_all_subscriptions()` 避免代码冗余，使用 Setting 表存储开关状态，前端使用轮询机制显示执行结果

**Tech Stack:** Flask, APScheduler, SQLite, Tailwind CSS, Vanilla JS

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `app/__init__.py` | 启动时加载 `scheduler_enabled` |
| `app/core/checker.py` | 新增 `_run_all_subscriptions()` 公共函数 |
| `app/scheduler/tasks.py` | 调用公共函数，添加开关检查 |
| `app/web/routes.py` | 处理开关保存 |
| `app/api/routes.py` | 调用公共函数，检查开关 |
| `config.py` | 添加 `SCHEDULER_ENABLED` 配置项 |
| `templates/settings.html` | 添加开关 UI |
| `templates/index.html` | 添加结果区域和手动执行按钮 |
| `static/js/app.js` | 添加轮询和结果显示逻辑 |

---

## Task 1: 添加配置项

**Files:**
- Modify: `config.py`

- [ ] **Step 1: 在 config.py 添加 SCHEDULER_ENABLED 配置项**

在 `config.py` 的 `Config` 类中添加：

```python
SCHEDULER_ENABLED = True  # 定时任务开关，默认开启
```

- [ ] **Step 2: 提交**

```bash
git add config.py && git commit -m "feat: add SCHEDULER_ENABLED config"
```

---

## Task 2: 提取公共函数

**Files:**
- Modify: `app/core/checker.py`

- [ ] **Step 1: 在 checker.py 末尾添加 `_run_all_subscriptions()` 函数**

打开 `app/core/checker.py`，在文件末尾添加：

```python
def _run_all_subscriptions():
    """遍历所有活跃订阅并执行抓取，返回 (results, failed_count)"""
    from app.database.models import Subscription

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

- [ ] **Step 2: 提交**

```bash
git add app/core/checker.py && git commit -m "feat: extract _run_all_subscriptions() for code reuse"
```

---

## Task 3: 修改 API routes

**Files:**
- Modify: `app/api/routes.py`

- [ ] **Step 1: 修改 `trigger_fetch_all()` 函数**

找到 `@api_bp.route("/fetch-all", methods=["POST"])` 的 `trigger_fetch_all` 函数，替换为：

```python
@api_bp.route("/fetch-all", methods=["POST"])
def trigger_fetch_all():
    """手动触发所有订阅的爬取"""
    from app.core.checker import _run_all_subscriptions

    # 检查定时任务开关
    if not getattr(Config, 'SCHEDULER_ENABLED', True):
        return jsonify({"error": "定时任务已关闭，请在设置页面开启"}), 403

    task_id = TaskManager.create_task()
    task = TaskManager.get_task(task_id)

    results, failed_count = _run_all_subscriptions()

    task.results = results
    task.total = len(results)
    task.completed = len(results) - failed_count
    task.failed = failed_count
    task.status = "completed"
    task.finished_at = datetime.utcnow()

    return jsonify({"task_id": task_id})
```

- [ ] **Step 2: 提交**

```bash
git add app/api/routes.py && git commit -m "feat: use _run_all_subscriptions() in API endpoint"
```

---

## Task 4: 修改 Scheduler tasks

**Files:**
- Modify: `app/scheduler/tasks.py`

- [ ] **Step 1: 修改 `setup_scheduler()` 函数中的 `run_all_checks` 内部函数**

在 `setup_scheduler()` 中找到 `def run_all_checks():`，替换为：

```python
def run_all_checks():
    # 检查定时任务开关
    if not getattr(Config, 'SCHEDULER_ENABLED', True):
        return

    from app.core.checker import _run_all_subscriptions
    _run_all_subscriptions()
```

同样修改 `reschedule_job()` 中的 `run_all_checks()`。

- [ ] **Step 2: 提交**

```bash
git add app/scheduler/tasks.py && git commit -m "feat: refactor scheduler to use _run_all_subscriptions() and check toggle"
```

---

## Task 5: 修改 app/__init__.py 加载开关状态

**Files:**
- Modify: `app/__init__.py`

- [ ] **Step 1: 在加载 `default_interval_cron` 的位置，添加加载 `scheduler_enabled`**

在 `app/__init__.py` 中找到：

```python
cron_setting = Setting.query.get("default_interval_cron")
if cron_setting:
    Config.DEFAULT_INTERVAL_CRON = cron_setting.value
```

在这段代码后面添加：

```python
scheduler_enabled = Setting.query.get("scheduler_enabled")
if scheduler_enabled:
    Config.SCHEDULER_ENABLED = scheduler_enabled.value == "true"
```

- [ ] **Step 2: 提交**

```bash
git add app/__init__.py && git commit -m "feat: load scheduler_enabled from Setting table on startup"
```

---

## Task 6: 修改 settings 路由处理开关保存

**Files:**
- Modify: `app/web/routes.py`

- [ ] **Step 1: 在 `settings` 路由中处理 `scheduler_enabled` 的保存**

在 `settings` 路由的 `POST` 处理中，找到保存 `fetch_retry_count` 的代码后面，添加：

```python
scheduler_enabled = request.form.get("scheduler_enabled", "true")

enabled_setting = Setting.query.get("scheduler_enabled")
if enabled_setting:
    enabled_setting.value = scheduler_enabled
else:
    enabled_setting = Setting(key="scheduler_enabled", value=scheduler_enabled)
    db.session.add(enabled_setting)

Config.SCHEDULER_ENABLED = scheduler_enabled == "true"
```

同时需要导入 `Setting` 模型（如果还没导入）。

- [ ] **Step 2: 在 `GET` 中传递 `scheduler_enabled` 到模板**

在 `settings` 路由的 `GET` 返回中，添加：

```python
scheduler_enabled = Setting.query.get("scheduler_enabled")
return render_template("settings.html",
                       default_cron=Config.DEFAULT_INTERVAL_CRON,
                       fetch_retry_count=fetch_retry_count,
                       scheduler_enabled=scheduler_enabled.value if scheduler_enabled else "true")
```

- [ ] **Step 3: 提交**

```bash
git add app/web/routes.py && git commit -m "feat: handle scheduler_enabled in settings page"
```

---

## Task 7: 修改 settings.html 添加开关 UI

**Files:**
- Modify: `templates/settings.html`

- [ ] **Step 1: 在 cron 表达式输入区域下方添加 Toggle 开关**

在 `settings.html` 中找到 cron 表达式输入区域（大约在 29-31 行附近），在其下方添加：

```html
<div class="mt-4 flex items-center gap-3">
    <label class="relative inline-flex items-center cursor-pointer">
        <input type="checkbox" id="scheduler_enabled" name="scheduler_enabled" value="true"
               class="sr-only peer" {{ 'checked' if scheduler_enabled == 'true' else '' }}>
        <div class="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
    </label>
    <span class="text-sm text-gray-300">启用定时任务</span>
</div>
```

**注意**：checkbox 使用 `sr-only peer` 配合 Tailwind 的 peer 机制实现 Toggle 样式。

- [ ] **Step 2: 提交**

```bash
git add templates/settings.html && git commit -m "feat: add scheduler toggle switch to settings page"
```

---

## Task 8: 修改 index.html 添加手动执行按钮和结果区域

**Files:**
- Modify: `templates/index.html`

- [ ] **Step 1: 在订阅卡片列表上方添加结果区域和手动执行按钮**

在 `index.html` 中找到订阅卡片列表开始的位置（约第 22 行 `<div id="subscriptions">`），在其上方添加：

```html
<!-- 手动执行区域 -->
<div class="mb-4">
    <div id="fetch-result" class="hidden mb-3 p-4 rounded-lg bg-gray-800 border border-gray-700">
        <span id="fetch-result-text" class="text-sm"></span>
    </div>
    <button id="trigger-fetch-btn" onclick="triggerFetchAll()"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors">
        手动执行
    </button>
</div>
```

- [ ] **Step 2: 提交**

```bash
git add templates/index.html && git commit -m "feat: add manual fetch button and result area to index page"
```

---

## Task 9: 修改 app.js 添加前端逻辑

**Files:**
- Modify: `static/js/app.js`

- [ ] **Step 1: 在文件末尾添加 `triggerFetchAll()` 函数**

在 `app.js` 末尾添加：

```javascript
async function triggerFetchAll() {
    const btn = document.getElementById('trigger-fetch-btn');
    const resultDiv = document.getElementById('fetch-result');
    const resultText = document.getElementById('fetch-result-text');

    btn.disabled = true;
    btn.classList.add('opacity-50', 'cursor-not-allowed');
    btn.textContent = '执行中...';

    try {
        const response = await fetch('/api/fetch-all', { method: 'POST' });
        const data = await response.json();

        if (data.error) {
            resultText.innerHTML = `<span class="text-red-400">✗ ${data.error}</span>`;
            resultDiv.classList.remove('hidden');
            resultDiv.classList.remove('bg-gray-800');
            resultDiv.classList.add('bg-red-900/30', 'border-red-700');
            setTimeout(() => {
                resultDiv.classList.add('hidden');
            }, 3000);
            return;
        }

        const taskId = data.task_id;
        pollTaskStatus(taskId);

    } catch (error) {
        resultText.innerHTML = `<span class="text-red-400">✗ 请求失败: ${error.message}</span>`;
        resultDiv.classList.remove('hidden');
        resultDiv.classList.add('bg-red-900/30', 'border-red-700');
        setTimeout(() => {
            resultDiv.classList.add('hidden');
        }, 3000);
    } finally {
        btn.disabled = false;
        btn.classList.remove('opacity-50', 'cursor-not-allowed');
        btn.textContent = '手动执行';
    }
}

async function pollTaskStatus(taskId) {
    const resultDiv = document.getElementById('fetch-result');
    const resultText = document.getElementById('fetch-result-text');
    const btn = document.getElementById('trigger-fetch-btn');

    btn.textContent = '执行中...';

    const poll = async () => {
        const response = await fetch(`/api/fetch-all/${taskId}`);
        const data = await response.json();

        if (data.status === 'completed') {
            const failed = data.failed || 0;
            const completed = data.completed || 0;
            const total = data.total || 0;

            let html = '';
            if (failed > 0) {
                const failedNames = data.results
                    .filter(r => r.status === 'error')
                    .map(r => r.name)
                    .join('、');
                html = `<span class="text-green-400">✓ 成功 ${completed} 个</span>，<span class="text-red-400">✗ 失败：${failedNames}</span>`;
                resultDiv.classList.remove('bg-gray-800');
                resultDiv.classList.add('bg-red-900/30', 'border-red-700');
            } else {
                html = `<span class="text-green-400">✓ 成功 ${total} 个</span>`;
                resultDiv.classList.remove('bg-red-900/30', 'border-red-700');
                resultDiv.classList.add('bg-gray-800');
            }

            resultText.innerHTML = html;
            resultDiv.classList.remove('hidden');

            setTimeout(() => {
                resultDiv.classList.add('hidden');
                location.reload();
            }, 3000);

            return;
        }

        setTimeout(poll, 500);
    };

    poll();
}
```

- [ ] **Step 2: 提交**

```bash
git add static/js/app.js && git commit -m "feat: add triggerFetchAll and pollTaskStatus to app.js"
```

---

## Task 10: Playwright 全功能测试

**Files:**
- 无文件修改

- [ ] **Step 1: 启动开发服务器**

```bash
cd /Users/jasper/Documents/Code/MyProjects/VidSpectre && uv run python run.py &
sleep 3
```

- [ ] **Step 2: 使用 Playwright 测试定时任务开关**

打开浏览器测试以下场景：

1. 访问设置页面 http://localhost:5002/settings
2. 确认 Toggle 开关存在且默认开启
3. 关闭定时任务开关并保存
4. 访问订阅列表页面 http://localhost:5002/
5. 点击"手动执行"按钮
6. 确认显示"定时任务已关闭"错误信息
7. 返回设置页面，重新开启定时任务
8. 再次点击"手动执行"
9. 确认执行成功，显示成功信息

- [ ] **Step 3: 测试失败显示**

在订阅列表页面：
1. 点击"手动执行"按钮
2. 确认显示成功或失败信息
3. 如果有失败，确认失败订阅名称列表显示正确

- [ ] **Step 4: 关闭开发服务器**

```bash
pkill -f "python run.py" || true
```

---

## 自检清单

- [ ] Spec 覆盖：所有设计需求都有对应任务实现
- [ ] 占位符扫描：无 TBD/TODO/实现后续填充等占位符
- [ ] 类型一致性：函数签名、属性名称在各任务间一致
