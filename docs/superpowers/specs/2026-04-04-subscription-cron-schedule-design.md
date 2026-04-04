# 订阅定时爬取周期自定义设计

## 概述

为每个订阅项添加自定义爬取周期的功能，支持全局默认周期设置 + 每个订阅单独设置，同时在操作列提供手动触发爬取的按钮。

## 需求

1. **全局默认值** - 在设置页面配置 cron 表达式，所有新订阅默认使用这个值
2. **每个订阅单独周期** - 点击订阅行展开后设置，存 cron 表达式
3. **手动爬取按钮** - 在操作列，点击后静默执行
4. **存储** - 单一字段存 cron 表达式
5. **页面人性化** - 下拉框选预设 + 自定义输入

## 数据模型

### Subscription 表新增字段

```python
interval_cron = db.Column(db.String(50), default=None)  # None表示使用全局默认值
```

### Config 表/类新增

```python
# 全局默认爬取周期 (cron表达式)
DEFAULT_INTERVAL_CRON = "0 */6 * * *"  # 默认每6小时
```

## 全局设置页面

### 路由
- `GET /settings` - 设置页面
- `POST /settings` - 保存设置

### 页面内容
- Cron 表达式输入框（带预设下拉框）
- 预设选项：
  - 每小时 `0 * * * *`
  - 每6小时 `0 */6 * * *`
  - 每12小时 `0 */12 * * *`
  - 每天早上9点 `0 9 * * *`
  - 每天两次(9点和21点) `0 9,21 * * *`
  - 每周一、三、五 `0 9 * * 1,3,5`
  - 自定义 [输入框]
- 帮助说明：显示 cron 格式解释

### API
```python
@web_bp.route("/settings", methods=["GET", "POST"])
def settings():
    """全局设置页面"""
```

## 订阅列表页面改动

### 操作列新增爬取按钮
```html
<button class="btn btn-sm btn-outline-success fetch-btn"
        data-sub-id="{{ sub.id }}"
        title="立即爬取">
  🔄
</button>
```

### 展开行新增周期设置
```html
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
      <option value="custom">自定义</option>
    </select>
  </div>
  <div class="col-auto" style="display: none;">
    <input type="text" class="form-control form-select-sm custom-cron"
           data-sub-id="{{ sub.id }}"
           value="{{ sub.interval_cron or '' }}"
           placeholder="0 */6 * * *">
  </div>
</div>
```

### JavaScript 改动

1. 爬取按钮点击事件
```javascript
document.querySelectorAll('.fetch-btn').forEach(function(btn) {
  btn.addEventListener('click', function() {
    const subId = this.dataset.subId;
    this.disabled = true;
    this.textContent = '...';

    fetch(`/api/subscriptions/${subId}/fetch`, { method: 'POST' })
      .then(() => {
        this.disabled = false;
        this.textContent = '🔄';
      })
      .catch(() => {
        this.disabled = false;
        this.textContent = '🔄';
      });
  });
});
```

2. 周期选择器联动
```javascript
document.querySelectorAll('.interval-select').forEach(function(select) {
  select.addEventListener('change', function() {
    const subId = this.dataset.subId;
    const customInput = document.querySelector(`.custom-cron[data-sub-id="${subId}"]`);
    const wrapper = customInput.parentElement;

    if (this.value === 'custom') {
      wrapper.style.display = 'block';
      customInput.focus();
    } else {
      wrapper.style.display = 'none';
      saveInterval(subId, this.value);
    }
  });
});
```

## API 改动

### 获取/更新订阅周期

```python
@api_bp.route("/subscriptions/<int:sub_id>/interval", methods=["GET"])
def get_subscription_interval(sub_id):
    subscription = Subscription.query.get_or_404(sub_id)
    interval = subscription.interval_cron or Config.DEFAULT_INTERVAL_CRON
    return jsonify({"interval_cron": interval})

@api_bp.route("/subscriptions/<int:sub_id>/interval", methods=["PUT"])
def update_subscription_interval(sub_id):
    subscription = Subscription.query.get_or_404(sub_id)
    data = request.json
    subscription.interval_cron = data.get("interval_cron")
    db.session.commit()
    return jsonify({"success": True})
```

### 手动触发爬取

```python
@api_bp.route("/subscriptions/<int:sub_id>/fetch", methods=["POST"])
def fetch_subscription(sub_id):
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

        if result:
            latest = max(result.keys())
            subscription.latest_episode = str(latest)
            subscription.latest_update_time = datetime.utcnow()
            db.session.commit()
    finally:
        loop.close()

    return jsonify({"success": True})
```

## 后端调度改动

### 使用 croniter 解析 cron 表达式

```python
from croniter import croniter

def should_run_now(cron_expr):
    """检查是否应该现在执行"""
    now = datetime.now()
    cron = croniter(cron_expr, now)
    prev_run = cron.get_prev(datetime)
    return (now - prev_run).total_seconds() < 3600
```

### 修改 scheduled job

```python
def check_updates():
    subscriptions = Subscription.query.all()
    for sub in subscriptions:
        if sub.status != 'active':
            continue
        interval = sub.interval_cron or Config.DEFAULT_INTERVAL_CRON
        if should_run_now(interval):
            # 爬取...
```

## 依赖

```bash
pip install croniter
```

## 文件改动清单

1. `app/database/models.py` - 添加 interval_cron 字段
2. `config.py` - 添加 DEFAULT_INTERVAL_CRON
3. `app/web/routes.py` - 添加 /settings 路由
4. `app/api/routes.py` - 添加 /api/subscriptions/{id}/fetch, /api/subscriptions/{id}/interval
5. `templates/settings.html` - 新建设置页面模板
6. `templates/index.html` - 添加爬取按钮和展开行的周期设置
7. `app/scheduler/tasks.py` - 修改调度逻辑支持cron表达式

## 测试场景

1. 全局默认值为 `0 */6 * * *`，新订阅使用该值
2. 修改订阅单独周期为 `0 9 * * *`，爬取按钮触发后更新最新集数
3. 设置为 "自定义" 时显示输入框
4. interval_cron 为 None 时使用全局默认值