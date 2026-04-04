# 订阅定时爬取周期自定义实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为每个订阅项添加自定义爬取周期(cron)功能，支持全局默认周期设置 + 手动触发爬取按钮

**Architecture:**
- 数据库: Subscription 表添加 interval_cron 字段存储 cron 表达式
- 全局设置: /settings 页面配置 DEFAULT_INTERVAL_CRON
- 订阅设置: 展开行内设置单独周期
- API: 添加 /api/subscriptions/{id}/fetch 和 /api/subscriptions/{id}/interval
- 前端: 操作列添加爬取按钮

**Tech Stack:** Flask, SQLAlchemy, croniter

---

## 1. 安装依赖

- [ ] Step 1: 安装 croniter 库

```bash
pip install croniter
```

---

## 2. 数据模型改动

**Files:**
- Modify: `app/database/models.py`
- Modify: `config.py`

- [ ] **Step 1: 修改 config.py 添加全局默认 cron**

打开 `config.py`,在 Config 类中添加:

```python
# Scheduler settings
SCHEDULER_INTERVAL_HOURS = 6
DEFAULT_INTERVAL_CRON = "0 */6 * * *"  # 默认每6小时
```

- [ ] **Step 2: 修改 models.py 添加 interval_cron 字段**

打开 `app/database/models.py`,在 Subscription 类中添加:

```python
# 爬取周期 (cron表达式, None表示使用全局默认值)
interval_cron = db.Column(db.String(50))
```

同时更新 to_dict 方法:

```python
def to_dict(self):
    return {
        "id": self.id,
        "media_type": self.media_type,
        "media_name": self.media_name,
        "media_id": self.media_id,
        "source_plugin": self.source_plugin,
        "status": self.status,
        "created_at": self.created_at.isoformat() if self.created_at else None,
        "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        "latest_episode": self.latest_episode,
        "latest_update_time": self.latest_update_time.isoformat() if self.latest_update_time else None,
        "current_episode": self.current_episode,
        "search_keywords": self.search_keywords,
        "interval_cron": self.interval_cron,
    }
```

- [ ] **Step 3: 运行数据库迁移**

```bash
 flask db migrate -m "add interval_cron to subscription"
 flask db upgrade
```

或者手动添加字段(如果使用简单SQLite):

```bash
# 检查数据库
sqlite3 storage/vidspectre.db "PRAGMA table_info(subscription);"
# 添加列
sqlite3 storage/vidspectre.db "ALTER TABLE subscription ADD COLUMN interval_cron VARCHAR(50);"
```

---

## 3. 全局设置页面

**Files:**
- Create: `templates/settings.html`
- Modify: `templates/base.html`
- Modify: `app/web/routes.py`

- [ ] **Step 1: 修改 base.html 添加导航链接**

打开 `templates/base.html`,在导航栏添加:

```html
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('web.settings') }}">设置</a>
</li>
```

- [ ] **Step 2: 添加 web settings 路由**

打开 `app/web/routes.py`,在文件末尾添加:

```python
@web_bp.route("/settings", methods=["GET", "POST"])
def settings():
    """全局设置页面"""
    if request.method == "POST":
        default_cron = request.form.get("default_cron")
        # 保存到 config 或数据库
        Config.DEFAULT_INTERVAL_CRON = default_cron
        # 也可以写入文件持久化
        return redirect(url_for("web.settings"))

    return render_template("settings.html", default_cron=Config.DEFAULT_INTERVAL_CRON)
```

- [ ] **Step 3: 创建设置页面模板**

创建 `templates/settings.html`:

```html
{% extends "base.html" %}

{% block title %}设置 - VidSpectre{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h4>全局设置</h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">默认爬取周期 (Cron表达式)</label>
                        <div class="input-group">
                            <select class="form-select" id="preset-select" style="max-width: 200px;">
                                <option value="">选择预设...</option>
                                <option value="0 * * * *">每小时</option>
                                <option value="0 */6 * * *">每6小时</option>
                                <option value="0 */12 * * *">每12小时</option>
                                <option value="0 9 * * *">每天早上9点</option>
                                <option value="0 9,21 * * *">每天两次</option>
                                <option value="0 9 * * 1,3,5">每周一三五四</option>
                                <option value="custom">自定义</option>
                            </select>
                            <input type="text" name="default_cron" class="form-control"
                                   value="{{ default_cron }}" placeholder="0 */6 * * *">
                        </div>
                        <div class="form-text">
                            格式说明: 分 小时 日 月 周<br>
                            例: <code>0 */6 * * *</code> = 每6小时, <code>0 9 * * *</code> = 每天9点
                        </div>
                    </div>
                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-primary">保存</button>
                        <a href="{{ url_for('web.index') }}" class="btn btn-secondary">返回</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.getElementById('preset-select').addEventListener('change', function() {
    if (this.value && this.value !== 'custom') {
        document.querySelector('input[name="default_cron"]').value = this.value;
    }
});
</script>
{% endblock %}
```

---

## 4. API 改动

**Files:**
- Modify: `app/api/routes.py`

- [ ] **Step 1: 添加获取/更新订阅周期的 API**

打开 `app/api/routes.py`,添加:

```python
@api_bp.route("/subscriptions/<int:sub_id>/interval", methods=["GET"])
def get_subscription_interval(sub_id):
    """获取订阅的爬取周期"""
    subscription = Subscription.query.get_or_404(sub_id)
    interval = subscription.interval_cron or Config.DEFAULT_INTERVAL_CRON
    return jsonify({"interval_cron": interval})

@api_bp.route("/subscriptions/<int:sub_id>/interval", methods=["PUT"])
def update_subscription_interval(sub_id):
    """更新订阅的爬取周期"""
    subscription = Subscription.query.get_or_404(sub_id)
    data = request.json
    interval_cron = data.get("interval_cron")
    # None 或空字符串表示使用全局默认值
    subscription.interval_cron = interval_cron if interval_cron else None
    db.session.commit()
    return jsonify({"success": True})
```

- [ ] **Step 2: 添加手动触发爬取的 API**

添加:

```python
from datetime import datetime

@api_bp.route("/subscriptions/<int:sub_id>/fetch", methods=["POST"])
def fetch_subscription(sub_id):
    """手动触发单个订阅的爬取"""
    subscription = Subscription.query.get_or_404(sub_id)

    plugin = registry.get_data_source(subscription.source_plugin)
    if not plugin:
        return jsonify({"error": "Plugin not found"}), 404

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        if subscription.media_type == 'movie':
            result = loop.run_until_complete(plugin.get_movie_links(subscription.media_id))
        else:
            result = loop.run_until_complete(plugin.get_episode_links(subscription.media_id))

        # 更新最新集数和时间
        if result and result.keys():
            latest = max(result.keys())
            subscription.latest_episode = str(latest)
            subscription.latest_update_time = datetime.utcnow()
            db.session.commit()
    finally:
        loop.close()

    return jsonify({"success": True, "latest_episode": subscription.latest_episode})
```

---

## 5. 前端订阅列表改动

**Files:**
- Modify: `templates/index.html`
- Modify: `app/web/routes.py` (传递全局默认值到模板)

- [ ] **Step 1: 修改 web routes 传递全局默认值**

打开 `app/web/routes.py`,修改 index 函数:

```python
@web_bp.route("/")
def index():
    """Home page - subscription list"""
    subscriptions = Subscription.query.all()
    return render_template("index.html",
                     subscriptions=subscriptions,
                     default_cron=Config.DEFAULT_INTERVAL_CRON)
```

- [ ] **Step 2: 修改 index.html 添加爬取按钮和周期设置**

打开 `templates/index.html`:

1. 在操作列添加爬取按钮(在删除按钮前):

```html
<button class="btn btn-sm btn-outline-success fetch-btn"
        data-sub-id="{{ sub.id }}"
        title="立即爬取">
    🔄
</button>
```

2. 在展开行添加周期设置(在现有的剧集列表后面):

```html
<tr class="interval-row" id="interval-{{ sub.id }}" style="display: none;">
    <td colspan="5">
        <div class="p-3 bg-light rounded">
            <div class="row g-2 align-items-center">
                <div class="col-auto">
                    <label class="form-label mb-0">爬取周期:</label>
                </div>
                <div class="col-auto">
                    <select class="form-select form-select-sm interval-select"
                            data-sub-id="{{ sub.id }}">
                        <option value="0 * * * *" {% if sub.interval_cron=='0 * * * *' %}selected{% endif %}>每小时</option>
                        <option value="0 */6 * * *" {% if sub.interval_cron=='0 */6 * * *' %}selected{% endif %}>每6小时</option>
                        <option value="0 */12 * * *" {% if sub.interval_cron=='0 */12 * * *' %}selected{% endif %}>每12小时</option>
                        <option value="0 9 * * *" {% if sub.interval_cron=='0 9 * * *' %}selected{% endif %}>每天早上9点</option>
                        <option value="0 9,21 * * *" {% if sub.interval_cron=='0 9,21 * * *' %}selected{% endif %}>每天两次</option>
                        <option value="0 9 * * 1,3,5" {% if sub.interval_cron=='0 9 * * 1,3,5' %}selected{% endif %}>每周一三五四</option>
                        <option value="custom" {% if sub.interval_cron and sub.interval_cron not in ['0 * * * *','0 */6 * * *','0 */12 * * *','0 9 * * *','0 9,21 * * *','0 9 * * 1,3,5'] %}selected{% endif %}>自定义</option>
                    </select>
                </div>
                <div class="col-auto {% if not sub.interval_cron or sub.interval_cron in ['0 * * * *','0 */6 * * *','0 */12 * * *','0 9 * * *','0 9,21 * * *','0 9 * * 1,3,5'] %}d-none{% endif %}" >
                    <input type="text" class="form-control form-control-sm custom-cron"
                           data-sub-id="{{ sub.id }}"
                           value="{{ sub.interval_cron or default_cron }}"
                           placeholder="0 */6 * * *">
                </div>
            </div>
        </div>
    </td>
</tr>
```

- [ ] **Step 3: 添加 JavaScript 交互逻辑**

在 `{% block scripts %}` 中添加:

```javascript
// 爬取按钮
document.querySelectorAll('.fetch-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
        const subId = this.dataset.subId;
        const originalText = this.textContent;
        this.disabled = true;
        this.textContent = '...';

        fetch(`/api/subscriptions/${subId}/fetch`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                this.disabled = false;
                this.textContent = '✓';
                setTimeout(() => this.textContent = originalText, 1500);
            })
            .catch(() => {
                this.disabled = false;
                this.textContent = '✗';
                setTimeout(() => this.textContent = originalText, 1500);
            });
    });
});

// 周期选择器联动
document.querySelectorAll('.interval-select').forEach(function(select) {
    select.addEventListener('change', function() {
        const subId = this.dataset.subId;
        const customInput = document.querySelector(`.custom-cron[data-sub-id="${subId}"]`);
        const wrapper = customInput.parentElement;

        if (this.value === 'custom') {
            wrapper.classList.remove('d-none');
            customInput.focus();
        } else {
            wrapper.classList.add('d-none');
            saveInterval(subId, this.value);
        }
    });
});

// 保存周期函数
function saveInterval(subId, cron) {
    fetch(`/api/subscriptions/${subId}/interval`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ interval_cron: cron })
    });
}

// 自定义输入框失焦保存
document.querySelectorAll('.custom-cron').forEach(function(input) {
    input.addEventListener('blur', function() {
        const subId = this.dataset.subId;
        if (this.value.trim()) {
            saveInterval(subId, this.value.trim());
        }
    });
});

// 展开/收起按钮联动显示周期设置行
document.querySelectorAll('.toggle-episodes').forEach(function(btn) {
    btn.addEventListener('click', function() {
        const subId = this.dataset.subId;
        const intervalRow = document.getElementById(`interval-${subId}`);
        if (intervalRow) {
            if (this.textContent === '收起剧集') {
                intervalRow.style.display = 'table-row';
            } else {
                intervalRow.style.display = 'none';
            }
        }
    });
});
```

---

## 6. 调度器改动

**Files:**
- Modify: `app/scheduler/tasks.py`

- [ ] **Step 1: 修改调度器支持按订阅周期执行**

打开 `app/scheduler/tasks.py`,改为动态检查:

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from croniter import croniter
from datetime import datetime
from config import Config

scheduler = BackgroundScheduler()

def should_run_now(cron_expr):
    """检查是否应该现在执行"""
    now = datetime.now()
    cron = croniter(cron_expr, now)
    prev_run = cron.get_prev(datetime)
    # 如果最近一次执行在当前小时内，返回True
    return (now - prev_run).total_seconds() < 3600

def check_subscription(sub):
    """检查单个订阅"""
    from app.core.checker import run_check_for_subscription
    from app import db
    from app.database.models import Subscription

    # 获取实际使用的cron
    interval = sub.interval_cron or Config.DEFAULT_INTERVAL_CRON

    if should_run_now(interval):
        run_check_for_subscription(sub.id)

def setup_scheduler(app):
    """Setup scheduler - 每小时运行一次,动态检查每个订阅是否应该执行"""
    scheduler.add_job(
        func=lambda: with_app_context(app, run_all_checks),
        trigger=IntervalTrigger(hours=1),
        id="check_updates",
        name="Check subscription updates",
        replace_existing=True
    )

    if not scheduler.running:
        scheduler.start()

    return scheduler

def run_all_checks():
    """检查所有需要更新的订阅"""
    from app.database.models import Subscription
    from app.core.checker import run_check_for_subscription

    subscriptions = Subscription.query.filter_by(status='active').all()
    for sub in subscriptions:
        interval = sub.interval_cron or Config.DEFAULT_INTERVAL_CRON
        if should_run_now(interval):
            run_check_for_subscription(sub.id)

def with_app_context(app, func):
    """Run function with app context"""
    with app.app_context():
        return func()
```

- [ ] **Step 2: 添加 run_check_for_subscription 函数**

在 `app/core/checker.py` 中添加:

```python
def run_check_for_subscription(sub_id):
    """检查单个订阅"""
    from app import db
    from app.database.models import Subscription
    from plugins.registry import registry
    import asyncio

    subscription = Subscription.query.get(sub_id)
    if not subscription or subscription.status != 'active':
        return

    plugin = registry.get_data_source(subscription.source_plugin)
    if not plugin:
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        if subscription.media_type == 'movie':
            result = loop.run_until_complete(plugin.get_movie_links(subscription.media_id))
        else:
            result = loop.run_until_complete(plugin.get_episode_links(subscription.media_id))

        if result and result.keys():
            latest = max(result.keys())
            if subscription.latest_episode != str(latest):
                subscription.latest_episode = str(latest)
                subscription.latest_update_time = datetime.utcnow()
                db.session.commit()
    finally:
        loop.close()
```

---

## 测试验证

- [ ] 测试1: 访问 /settings 设置全局默认cron
- [ ] 测试2: 添加新订阅,interval_cron应为None(使用全局)
- [ ] 测试3: 点击订阅展开,设置自定义周期
- [ ] 测试4: 点击爬取按钮,验证latest_update_time更新
- [ ] 测试5: 验证重启后cron保存持久化(可选:写入文件)

---

## 文件改动清单

| 文件 | 操作 |
|------|------|
| config.py | 修改: 添加 DEFAULT_INTERVAL_CRON |
| app/database/models.py | 修改: 添加 interval_cron 字段,更新 to_dict |
| app/web/routes.py | 修改: 传递 default_cron,添加 /settings 路由 |
| app/api/routes.py | 修改: 添加 fetch/interval API |
| app/core/checker.py | 修改: 添加 run_check_for_subscription |
| app/scheduler/tasks.py | 修改: 支持cron动态调度 |
| templates/base.html | 修改: 添加设置导航链接 |
| templates/settings.html | 新建: 设置页面模板 |
| templates/index.html | 修改: 添加爬取按钮和周期设置 |