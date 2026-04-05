# 电影爬取优化实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 优化搜索结果 UI（添加封面图、移除标签）和电影展开交互（直接显示资源列表）

**Architecture:**
1. `searchMedia()` JS 函数：渲染搜索结果时添加封面图、移除类型标签
2. `toggleEpisodes()` JS 函数：根据 `media_type` 区分电影/电视剧展开行为
3. 订阅卡片模板：为电影添加展开按钮，传递 `media_type` 属性

**Tech Stack:** Vanilla JavaScript, Flask Jinja2 templates

---

## 改动文件清单

| 文件 | 改动内容 |
|------|---------|
| `static/js/app.js` | 1. `searchMedia()` 添加封面图，移除标签<br>2. `toggleEpisodes()` + `renderMovieLinks()` 处理电影逻辑 |
| `templates/index.html` | 1. 为电影添加展开按钮<br>2. 按钮添加 `data-media-type` 属性 |
| `templates/subscription.html` | 已完成：搜索模块移到最上面 |

---

## Task 1: 搜索结果添加封面图，移除类型标签

**Files:**
- Modify: `static/js/app.js:283-301` (searchMedia 函数渲染逻辑)

- [ ] **Step 1: 修改 searchMedia 渲染逻辑**

替换当前搜索结果渲染代码（lines 283-301）：

```javascript
data.forEach(item => {
    const div = document.createElement('div');
    div.className = 'p-3 border-b border-gray-700 cursor-pointer hover:bg-gray-700 flex items-center gap-3';
    // Cover image
    const img = document.createElement('img');
    img.src = item.cover_url || '';
    img.className = 'w-12 h-12 object-cover rounded flex-shrink-0 bg-gray-600';
    img.onerror = function() {
        this.style.display = 'none';
        this.nextElementSibling.style.display = 'flex';
    };
    const placeholder = document.createElement('div');
    placeholder.className = 'w-12 h-12 rounded flex-shrink-0 bg-gray-600 hidden items-center justify-center text-gray-400 text-xs';
    placeholder.textContent = '无图';
    div.appendChild(img);
    div.appendChild(placeholder);
    // Name
    const nameSpan = document.createElement('span');
    nameSpan.className = 'font-medium flex-1 truncate';
    nameSpan.textContent = item.name;
    div.appendChild(nameSpan);
    div.addEventListener('click', function() {
        document.querySelector('input[name="media_name"]').value = item.name;
        document.querySelector('input[name="media_id"]').value = item.media_id;
        resultsDiv.innerHTML = '';
    });
    resultsDiv.appendChild(div);
});
```

- [ ] **Step 2: 测试搜索功能**

Run: 启动 Flask 开发服务器 `uv run python run.py`
验证:
- 搜索关键词如"盗梦空间"
- 搜索结果显示封面图片
- 搜索结果不显示"电影"或"电视剧"标签

---

## Task 2: 为电影订阅添加展开按钮

**Files:**
- Modify: `templates/index.html:38-45`

- [ ] **Step 1: 添加电影展开按钮条件**

当前代码（line 38）:
```jinja
{% if sub.media_type == 'tv' and sub.media_id %}
```

修改为:
```jinja
{% if sub.media_id %}
```

这样电影和电视剧都会显示展开按钮（只要有 media_id）。

- [ ] **Step 2: 为按钮添加 data-media-type 属性**

当前代码（lines 39-44）:
```html
<button class="toggle-episodes ml-2 ..."
        data-sub-id="{{ sub.id }}"
        data-media-id="{{ sub.media_id }}"
        data-source="{{ sub.source_plugin }}">
```

修改为:
```html
<button class="toggle-episodes ml-2 ..."
        data-sub-id="{{ sub.id }}"
        data-media-id="{{ sub.media_id }}"
        data-source="{{ sub.source_plugin }}"
        data-media-type="{{ sub.media_type }}">
```

- [ ] **Step 3: 验证**

Run: 访问首页，确认电影和电视剧都有展开按钮

---

## Task 3: 实现电影展开直接显示资源逻辑

**Files:**
- Modify: `static/js/app.js:95-118` (toggleEpisodes 函数)
- Add: `static/js/app.js` (renderMovieLinks 函数)

- [ ] **Step 1: 修改 toggleEpisodes 函数开头**

在 `toggleEpisodes` 函数获取元素后、fetch 之前添加 movie 判断：

```javascript
function toggleEpisodes(btn) {
    const subId = btn.dataset.subId;
    const row = document.getElementById('episodes-' + subId);
    const content = document.getElementById('episodes-content-' + subId);
    const loading = row ? row.querySelector('.episodes-loading') : null;
    const mediaType = btn.dataset.mediaType || 'tv';  // 新增

    if (row && row.style.display === 'none') {
        row.style.display = 'block';
        btn.textContent = '收起';

        // 电影类型：直接获取资源列表
        if (mediaType === 'movie') {
            fetch(`/api/subscriptions/${subId}/movie-links`)
                .then(r => r.json())
                .then(links => {
                    if (loading) loading.style.display = 'none';
                    renderMovieLinks(links, subId);
                })
                .catch(err => {
                    if (loading) loading.textContent = '加载失败';
                });
            return;
        }

        // 电视剧类型：原有逻辑
        fetch(`/api/subscriptions/${subId}/episodes`)
            .then(r => r.json())
            .then(episodes => {
                if (loading) loading.style.display = 'none';
                renderEpisodes(episodes, subId);
            })
            .catch(err => {
                if (loading) loading.textContent = '加载失败';
            });
    } else if (row) {
        row.style.display = 'none';
        btn.textContent = '展开';
    }
}
```

- [ ] **Step 2: 添加 renderMovieLinks 函数**

在 `renderEpisodes` 函数之后添加：

```javascript
function renderMovieLinks(links, subId) {
    const content = document.getElementById('episodes-content-' + subId);
    if (!links || links.length === 0) {
        content.innerHTML = '<p class="text-gray-400">暂无可用资源</p>';
        return;
    }
    let html = '<div class="space-y-2">';
    links.forEach(link => {
        html += `
        <button class="get-magnet-link w-full text-left px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm text-blue-400 hover:text-blue-300"
                data-url="${escapeHtml(link.url)}"
                data-title="${escapeHtml(link.title || link.name || '')}">
            ${escapeHtml(link.title || link.name || '下载链接')}
        </button>`;
    });
    html += '</div>';
    content.innerHTML = html;

    // 绑定点击事件
    content.querySelectorAll('.get-magnet-link').forEach(linkBtn => {
        linkBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const originalText = this.textContent;
            this.textContent = '获取中...';
            const existingDisplay = this.parentElement.querySelector('.magnet-display');
            if (existingDisplay) existingDisplay.remove();
            const url = this.dataset.url;
            if (url.startsWith('magnet:')) {
                const magnetHtml = `<div class="magnet-display mt-2 p-2 bg-gray-750 rounded break-all">
                    <a href="${escapeHtml(url)}" class="text-blue-400 hover:text-blue-300 text-sm break-all">${escapeHtml(url)}</a>
                </div>`;
                this.insertAdjacentHTML('afterend', magnetHtml);
            }
            this.textContent = originalText;
        });
    });
}
```

- [ ] **Step 3: 添加 movie-links API 路由**

Modify: `app/api/routes.py` (在 `get_episodes` 路由之后添加新路由)

```python
@api_bp.route("/subscriptions/<int:sub_id>/movie-links", methods=["GET"])
def get_movie_links(sub_id):
    """Get all download links for a movie subscription"""
    subscription = Subscription.query.get_or_404(sub_id)

    if subscription.media_type != 'movie':
        return jsonify({"error": "Not a movie subscription"}), 400

    plugin = registry.get_data_source(subscription.source_plugin)
    if not plugin:
        return jsonify({"error": "Plugin not found"}), 404

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        links = loop.run_until_complete(plugin.get_download_links(subscription.media_id))
    finally:
        loop.close()

    # Filter by keywords if set
    keywords = subscription.search_keywords or ""
    keyword_list = [k.strip().lower() for k in keywords.split(",") if k.strip()]
    if keyword_list:
        links = [link for link in links
                 if all(k in link.get("title", "").lower() for k in keyword_list)]

    return jsonify([{
        "title": link.get("title", ""),
        "url": link.get("url", ""),
        "type": link.get("type", "")
    } for link in links])
```

- [ ] **Step 4: 确认 Btbtla 插件有 get_download_links 方法**

检查: `plugins/sources/btbtla/plugin.py`

确认有:
```python
async def get_download_links(self, media_id: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, self.parser.get_download_links, media_id)
```

- [ ] **Step 5: 测试电影展开功能**

Run: 启动服务器，添加一个电影订阅
1. 点击电影的展开按钮
2. 验证直接显示资源列表（无集数选择）
3. 点击资源，验证显示磁力链接

---

## Task 4: 提交代码

- [ ] **Step 1: 提交所有改动**

```bash
git add static/js/app.js templates/index.html app/api/routes.py
git commit -m "$(cat <<'EOF'
feat: add cover images to search results and movie expand interaction

- Search results now show cover images, type badges removed
- Movies now have expand button that shows resources directly
- New /api/subscriptions/{id}/movie-links endpoint for movie resources
- Movies skip episode selection and display download links directly

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## 自检清单

- [ ] Spec 覆盖检查：搜索结果封面图 ✓，移除标签 ✓，电影展开直接显示资源 ✓
- [ ] 无 placeholder：所有代码已提供
- [ ] 类型一致性：API 返回格式与 `renderMovieLinks` 期望格式一致
- [ ] 任务粒度：每个任务 2-5 分钟可完成

---

**Plan complete.** Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
