# VidSpectre 前端移动端重构实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 VidSpectre 前端从 Bootstrap 5 迁移到 Tailwind CSS，实现移动端优先的响应式设计

**Architecture:** 前端完全重写，使用 Tailwind CSS Play CDN 无需构建。JavaScript 提取到独立文件 `static/js/app.js`，使用 `addEventListener` 替代内联 onclick。深色主题通过 Tailwind `dark:` 变体和 `<html class="dark">` 实现。

**Tech Stack:** Tailwind CSS v3 (Play CDN), Vanilla JavaScript (ES6+), Flask/Jinja2 templates

---

## 文件结构

```
static/                          # 新建
└── js/
    └── app.js                   # 所有 JS 逻辑

templates/
├── base.html                    # 重写: 引入 Tailwind + app.js
├── index.html                   # 重写: 卡片布局
├── subscription.html           # 重写: Tailwind 表单
├── edit_subscription.html       # 重写: Tailwind 表单
└── settings.html                # 重写: Tailwind 表单
```

---

## Task 1: 创建 static/js/app.js 骨架

**Files:**
- Create: `static/js/app.js`

- [ ] **Step 1: 创建目录和空文件骨架**

```bash
mkdir -p /Users/jasper/Documents/Code/VidSpectre/static/js
touch /Users/jasper/Documents/Code/VidSpectre/static/js/app.js
```

- [ ] **Step 2: 写入基础 JS 骨架**

```javascript
/**
 * VidSpectre Frontend - Mobile-First Refactor
 * Uses Tailwind CSS + vanilla JavaScript
 */

// Global functions exposed on window
window.fetchSubscription = fetchSubscription;
window.saveSubscription = saveSubscription;
window.toggleEpisodes = toggleEpisodes;

function fetchSubscription(btn) {
    const subId = btn.dataset.subId;
    btn.disabled = true;
    btn.textContent = '...';

    saveSubscription(subId)
        .then(() => {
            return fetch(`/api/subscriptions/${subId}/fetch`, { method: 'POST' });
        })
        .then(response => response.json())
        .then(data => {
            const row = btn.closest('.subscription-card');
            const latestCell = row.querySelector('.latest-episode');
            if (data.latest_episode && latestCell) {
                latestCell.textContent = data.latest_episode;
            }
            const episodesContent = document.getElementById('episodes-content-' + subId);
            const episodesRow = document.getElementById('episodes-' + subId);
            if (episodesContent && episodesRow && episodesRow.style.display !== 'none') {
                episodesContent.innerHTML = '';
                fetch(`/api/subscriptions/${subId}/episodes`)
                    .then(r => r.json())
                    .then(episodes => renderEpisodes(episodes, subId));
            }
        })
        .then(() => {
            btn.textContent = '✓';
        })
        .catch(() => {
            btn.textContent = '✗';
        })
        .finally(() => {
            btn.disabled = false;
            setTimeout(() => btn.textContent = '🔄', 1500);
        });
}

function saveSubscription(subId) {
    const episodeInput = document.querySelector(`.episode-input[data-sub-id="${subId}"]`);
    const keywordsInput = document.querySelector(`.keywords-input[data-sub-id="${subId}"]`);
    const currentEpisode = episodeInput ? episodeInput.value.trim() : '';
    const searchKeywords = keywordsInput ? keywordsInput.value.trim() : '';

    return fetch(`/api/subscriptions/${subId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_episode: currentEpisode, search_keywords: searchKeywords })
    })
    .then(response => response.json())
    .then(data => {
        if (episodeInput) {
            episodeInput.classList.add('border-green-500');
            setTimeout(() => episodeInput.classList.remove('border-green-500'), 1000);
        }
        if (keywordsInput) {
            keywordsInput.classList.add('border-green-500');
            setTimeout(() => keywordsInput.classList.remove('border-green-500'), 1000);
        }
    });
}

function toggleEpisodes(btn) {
    const subId = btn.dataset.subId;
    const row = document.getElementById('episodes-' + subId);
    const content = document.getElementById('episodes-content-' + subId);
    const loading = row ? row.querySelector('.episodes-loading') : null;

    if (row && row.style.display === 'none') {
        row.style.display = 'block';
        btn.textContent = '收起';

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

function renderEpisodes(episodes, subId) {
    const content = document.getElementById('episodes-content-' + subId);
    if (Object.keys(episodes).length === 0) {
        content.innerHTML = '<p class="text-gray-400">暂无可用剧集</p>';
        return;
    }
    const sorted = Object.keys(episodes).sort((a, b) => b - a);
    let html = '<div class="space-y-3">';
    sorted.forEach(ep => {
        const links = episodes[ep];
        html += `
        <div class="border-b border-gray-700 pb-2">
            <div class="flex justify-between items-center">
                <span class="font-medium">第${ep}集</span>
                <button class="get-magnet-link text-blue-400 hover:text-blue-300 text-sm"
                        data-url="${links[0].url}"
                        data-title="${links[0].title.substring(0, 30)}">
                    获取
                </button>
            </div>
        </div>`;
    });
    html += '</div>';
    content.innerHTML = html;

    content.querySelectorAll('.get-magnet-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            this.textContent = '获取中...';
            fetch('/api/download-link?url=' + encodeURIComponent(this.dataset.url))
                .then(r => r.json())
                .then(d => {
                    if (d.magnet) {
                        prompt('磁力链接:', d.magnet);
                        this.textContent = '获取';
                    } else {
                        alert('获取失败');
                        this.textContent = this.dataset.title;
                    }
                })
                .catch(() => {
                    alert('获取失败');
                    this.textContent = '获取';
                });
        });
    });
}

// Initialization functions
function initSaveButtons() {
    document.querySelectorAll('.save-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const subId = this.dataset.subId;
            saveSubscription(subId);
        });
    });
}

function initFetchButtons() {
    document.querySelectorAll('.fetch-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            fetchSubscription(this);
        });
    });
}

function initEpisodeToggles() {
    document.querySelectorAll('.toggle-episodes').forEach(btn => {
        btn.addEventListener('click', function() {
            toggleEpisodes(this);
        });
    });
}

function initDeleteForms() {
    document.querySelectorAll('.delete-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('确定删除？')) {
                e.preventDefault();
            }
        });
    });
}

function initIntervalSelectors() {
    document.querySelectorAll('.interval-select').forEach(select => {
        select.addEventListener('change', function() {
            const subId = this.dataset.subId;
            const customInput = document.querySelector(`.custom-cron[data-sub-id="${subId}"]`);
            const wrapper = customInput ? customInput.parentElement : null;

            if (this.value === 'custom') {
                wrapper && wrapper.classList.remove('hidden');
                customInput && customInput.focus();
            } else {
                wrapper && wrapper.classList.add('hidden');
                saveInterval(subId, this.value);
            }
        });
    });

    document.querySelectorAll('.custom-cron').forEach(input => {
        input.addEventListener('blur', function() {
            const subId = this.dataset.subId;
            if (this.value.trim()) {
                saveInterval(subId, this.value.trim());
            }
        });
    });
}

function saveInterval(subId, cron) {
    fetch(`/api/subscriptions/${subId}/interval`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ interval_cron: cron })
    });
}

function initMoreMenus() {
    document.querySelectorAll('.more-menu-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const menu = this.nextElementSibling;
            document.querySelectorAll('.more-menu').forEach(m => {
                if (m !== menu) m.classList.add('hidden');
            });
            menu.classList.toggle('hidden');
        });
    });

    document.addEventListener('click', function() {
        document.querySelectorAll('.more-menu').forEach(m => m.classList.add('hidden'));
    });
}

function initSearchKeyword() {
    const input = document.getElementById('search-keyword');
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchMedia();
            }
        });
    }
}

function searchMedia() {
    const keyword = document.getElementById('search-keyword').value.trim();
    if (!keyword) return;

    const resultsDiv = document.getElementById('search-results');
    resultsDiv.innerHTML = '<div class="p-3 text-gray-400">搜索中...</div>';

    fetch('/api/search?q=' + encodeURIComponent(keyword))
        .then(response => response.json())
        .then(data => {
            resultsDiv.innerHTML = '';
            if (data.length === 0) {
                resultsDiv.innerHTML = '<div class="p-3 text-gray-400">未找到结果</div>';
                return;
            }
            data.forEach(item => {
                const badge = item.media_type === 'movie' ? '电影' : '电视剧';
                const div = document.createElement('div');
                div.className = 'p-3 border-b border-gray-700 cursor-pointer hover:bg-gray-700';
                div.innerHTML = `<span class="font-medium">${item.name}</span> <span class="text-xs bg-gray-600 px-2 py-1 rounded">${badge}</span>`;
                div.addEventListener('click', function() {
                    document.querySelector('input[name="media_name"]').value = item.name;
                    document.querySelector('input[name="media_id"]').value = item.media_id;
                    resultsDiv.innerHTML = '';
                });
                resultsDiv.appendChild(div);
            });
        })
        .catch(err => {
            resultsDiv.innerHTML = '<div class="p-3 text-red-400">搜索失败</div>';
        });
}

window.searchMedia = searchMedia;

// DOMContentLoaded initialization
document.addEventListener('DOMContentLoaded', function() {
    initSaveButtons();
    initFetchButtons();
    initEpisodeToggles();
    initDeleteForms();
    initIntervalSelectors();
    initMoreMenus();
    initSearchKeyword();
});
```

- [ ] **Step 3: Commit**

```bash
git add static/js/app.js
git commit -m "feat: create static/js/app.js skeleton with all event handlers"
```

---

## Task 2: 重写 base.html

**Files:**
- Modify: `templates/base.html`

- [ ] **Step 1: 读取当前 base.html 确认内容**

```bash
cat /Users/jasper/Documents/Code/VidSpectre/templates/base.html
```

- [ ] **Step 2: 重写 base.html 使用 Tailwind CDN**

```html
<!DOCTYPE html>
<html lang="zh-CN" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}VidSpectre{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
        }
    </script>
</head>
<body class="bg-gray-900 text-gray-100 min-h-screen">
    <nav class="bg-gray-800 border-b border-gray-700">
        <div class="container mx-auto px-4">
            <div class="flex justify-between items-center h-16">
                <a class="text-xl font-bold text-white" href="{{ url_for('web.index') }}">VidSpectre</a>
                <button id="mobile-menu-btn" class="md:hidden p-2 rounded-lg hover:bg-gray-700">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
                    </svg>
                </button>
                <div class="hidden md:flex items-center space-x-4">
                    <a class="px-3 py-2 rounded-lg hover:bg-gray-700" href="{{ url_for('web.index') }}">订阅列表</a>
                    <a class="px-3 py-2 rounded-lg hover:bg-gray-700" href="{{ url_for('web.add_subscription') }}">添加订阅</a>
                    <a class="px-3 py-2 rounded-lg hover:bg-gray-700" href="{{ url_for('web.settings') }}">设置</a>
                </div>
            </div>
        </div>
        <!-- Mobile menu -->
        <div id="mobile-menu" class="hidden md:hidden border-t border-gray-700">
            <div class="px-4 py-2 space-y-2">
                <a class="block px-3 py-2 rounded-lg hover:bg-gray-700" href="{{ url_for('web.index') }}">订阅列表</a>
                <a class="block px-3 py-2 rounded-lg hover:bg-gray-700" href="{{ url_for('web.add_subscription') }}">添加订阅</a>
                <a class="block px-3 py-2 rounded-lg hover:bg-gray-700" href="{{ url_for('web.settings') }}">设置</a>
            </div>
        </div>
    </nav>

    <main class="container mx-auto px-4 py-6">
        {% block content %}{% endblock %}
    </main>

    <script src="{{ url_for('static', filename='js/app.js') }}"></script>
    <script>
        // Mobile menu toggle
        document.getElementById('mobile-menu-btn').addEventListener('click', function() {
            document.getElementById('mobile-menu').classList.toggle('hidden');
        });
    </script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

- [ ] **Step 3: Commit**

```bash
git add templates/base.html
git commit -m "feat: rewrite base.html with Tailwind CSS and dark mode"
```

---

## Task 3: 重写 index.html (订阅列表页)

**Files:**
- Modify: `templates/index.html`

- [ ] **Step 1: 读取当前 index.html**

```bash
cat /Users/jasper/Documents/Code/VidSpectre/templates/index.html
```

- [ ] **Step 2: 重写 index.html 使用卡片布局**

```html
{% extends "base.html" %}

{% block title %}订阅列表 - VidSpectre{% endblock %}

{% block content %}
<div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold">我的订阅</h1>
    <a href="{{ url_for('web.add_subscription') }}" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg">
        添加订阅
    </a>
</div>

{% if subscriptions %}
<div class="space-y-4">
    {% for sub in subscriptions %}
    <!-- Subscription Card -->
    <div class="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden subscription-card">
        <!-- Card Header -->
        <div class="p-4 flex justify-between items-start">
            <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                    {% if sub.media_type == 'movie' %}
                    <span class="bg-blue-600 text-xs px-2 py-0.5 rounded">电影</span>
                    {% else %}
                    <span class="bg-green-600 text-xs px-2 py-0.5 rounded">电视剧</span>
                    {% endif %}
                    {% if not sub.media_id %}
                    <span class="text-yellow-400 text-xs" title="资源未找到，请在添加订阅时搜索并选择正确的资源">⚠</span>
                    {% endif %}
                </div>
                <h3 class="text-lg font-medium truncate">{{ sub.media_name }}</h3>
            </div>
            {% if sub.media_type == 'tv' and sub.media_id %}
            <button class="toggle-episodes ml-2 text-sm text-blue-400 hover:text-blue-300"
                    data-sub-id="{{ sub.id }}"
                    data-media-id="{{ sub.media_id }}"
                    data-source="{{ sub.source_plugin }}">
                展开
            </button>
            {% endif %}
        </div>

        <!-- Card Body -->
        <div class="px-4 pb-2 text-sm text-gray-400">
            <div class="flex flex-wrap gap-4">
                {% if sub.media_type == 'tv' %}
                <div>
                    <span class="text-gray-500">看到:</span>
                    <input type="text"
                           class="episode-input bg-gray-700 border border-gray-600 rounded px-2 py-1 w-16 text-white"
                           value="{{ sub.current_episode or '' }}"
                           placeholder="集数"
                           data-sub-id="{{ sub.id }}">
                </div>
                {% endif %}
                <div>
                    <span class="text-gray-500">关键字:</span>
                    <input type="text"
                           class="keywords-input bg-gray-700 border border-gray-600 rounded px-2 py-1 w-32 text-white"
                           value="{{ sub.search_keywords or '' }}"
                           placeholder="关键字"
                           data-sub-id="{{ sub.id }}">
                </div>
                <div>
                    <span class="text-gray-500">最新:</span>
                    <span class="latest-episode">{{ sub.latest_episode or '-' }}</span>
                </div>
            </div>
        </div>

        <!-- Card Actions -->
        <div class="px-4 py-3 bg-gray-750 border-t border-gray-700 flex items-center justify-between">
            <button class="fetch-btn bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium"
                    data-sub-id="{{ sub.id }}">
                🔄 爬取
            </button>
            <div class="relative">
                <button class="more-menu-btn bg-gray-600 hover:bg-gray-500 text-white px-3 py-2 rounded-lg">
                    ⋯ 更多
                </button>
                <div class="more-menu hidden absolute right-0 mt-2 w-36 bg-gray-700 rounded-lg shadow-lg border border-gray-600 z-10">
                    <button class="save-btn w-full text-left px-4 py-2 hover:bg-gray-600 rounded-t-lg"
                            data-sub-id="{{ sub.id }}">
                        💾 保存
                    </button>
                    <a href="{{ url_for('web.edit_subscription', sub_id=sub.id) }}"
                       class="block px-4 py-2 hover:bg-gray-600">
                        ✏️ 编辑
                    </a>
                    <form class="delete-form" action="{{ url_for('web.delete_subscription', sub_id=sub.id) }}" method="POST">
                        <button type="submit" class="w-full text-left px-4 py-2 hover:bg-gray-600 text-red-400 rounded-b-lg">
                            🗑️ 删除
                        </button>
                    </form>
                </div>
            </div>
        </div>

        <!-- Episodes Expandable Section -->
        {% if sub.media_type == 'tv' %}
        <div id="episodes-{{ sub.id }}" style="display: none;" class="border-t border-gray-700">
            <div class="p-4 bg-gray-750">
                <div class="flex justify-between items-center mb-3">
                    <h6 class="font-medium text-gray-300">剧集列表</h6>
                    <button class="close-episodes text-gray-400 hover:text-white"
                            data-sub-id="{{ sub.id }}">
                        ✕
                    </button>
                </div>
                <div class="episodes-loading text-gray-400">加载中...</div>
                <div id="episodes-content-{{ sub.id }}"></div>

                <!-- Interval Selector -->
                <div class="mt-4 pt-4 border-t border-gray-600">
                    <div class="flex items-center gap-2">
                        <label class="text-sm text-gray-400">爬取周期:</label>
                        <select class="interval-select bg-gray-700 border border-gray-600 rounded px-3 py-1.5 text-sm"
                                data-sub-id="{{ sub.id }}">
                            <option value="0 * * * *" {% if sub.interval_cron=='0 * * * *' %}selected{% endif %}>每小时</option>
                            <option value="0 */6 * * *" {% if sub.interval_cron=='0 */6 * * *' %}selected{% endif %}>每6小时</option>
                            <option value="0 */12 * * *" {% if sub.interval_cron=='0 */12 * * *' %}selected{% endif %}>每12小时</option>
                            <option value="0 9 * * *" {% if sub.interval_cron=='0 9 * * *' %}selected{% endif %}>每天早上9点</option>
                            <option value="0 9,21 * * *" {% if sub.interval_cron=='0 9,21 * * *' %}selected{% endif %}>每天两次</option>
                            <option value="0 9 * * 1,3,5" {% if sub.interval_cron=='0 9 * * 1,3,5' %}selected{% endif %}>每周一三五四</option>
                            <option value="custom" {% if sub.interval_cron and sub.interval_cron not in ['0 * * * *','0 */6 * * *','0 */12 * * *','0 9 * * *','0 9,21 * * *','0 9 * * 1,3,5'] %}selected{% endif %}>自定义</option>
                        </select>
                        <input type="text"
                               class="custom-cron hidden bg-gray-700 border border-gray-600 rounded px-2 py-1.5 text-sm w-32"
                               data-sub-id="{{ sub.id }}"
                               value="{{ sub.interval_cron or default_cron }}"
                               placeholder="0 */6 * * *">
                    </div>
                </div>
            </div>
        </div>
        {% endif %}
    </div>
    {% endfor %}
</div>
{% else %}
<div class="bg-gray-800 rounded-lg p-8 text-center border border-gray-700">
    <p class="text-gray-400 mb-4">暂无订阅</p>
    <a href="{{ url_for('web.add_subscription') }}" class="text-blue-400 hover:text-blue-300">点击添加</a>
</div>
{% endif %}
{% endblock %}
```

- [ ] **Step 3: Commit**

```bash
git add templates/index.html
git commit -m "feat: rewrite index.html with Tailwind card layout"
```

---

## Task 4: 重写 subscription.html (添加订阅页)

**Files:**
- Modify: `templates/subscription.html`

- [ ] **Step 1: 重写 subscription.html**

```html
{% extends "base.html" %}

{% block title %}添加订阅 - VidSpectre{% endblock %}

{% block content %}
<div class="max-w-2xl mx-auto">
    <div class="bg-gray-800 rounded-lg border border-gray-700">
        <div class="px-6 py-4 border-b border-gray-700">
            <h2 class="text-xl font-bold">添加订阅</h2>
        </div>
        <div class="p-6">
            <form method="POST" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1">媒体类型</label>
                    <select name="media_type" class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white">
                        <option value="movie">电影</option>
                        <option value="tv" selected>电视剧</option>
                    </select>
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1">名称</label>
                    <input type="text" name="media_name" required
                           class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white">
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1">资源 ID（可选）</label>
                    <input type="text" name="media_id"
                           class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                           placeholder="留空稍后通过搜索设置">
                    <p class="text-xs text-gray-500 mt-1">或者通过下方的搜索功能选择资源</p>
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1">数据源</label>
                    <select name="source_plugin" class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white">
                        <option value="btbtla" selected>btbtla</option>
                    </select>
                </div>

                <hr class="border-gray-700">

                <h3 class="text-lg font-medium text-gray-200">搜索资源</h3>
                <p class="text-sm text-gray-500">搜索并选择正确的资源，它会自动填充上面的"名称"和"资源 ID"</p>

                <div class="flex gap-2">
                    <input type="text" id="search-keyword"
                           class="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                           placeholder="输入剧名搜索...">
                    <button type="button" onclick="searchMedia()"
                            class="bg-gray-600 hover:bg-gray-500 text-white px-4 py-2 rounded-lg">
                        搜索
                    </button>
                </div>
                <div id="search-results" class="bg-gray-700 rounded-lg overflow-hidden"></div>

                <div class="flex gap-3 pt-4">
                    <button type="submit"
                            class="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium">
                        添加
                    </button>
                    <a href="{{ url_for('web.index') }}"
                       class="flex-1 bg-gray-600 hover:bg-gray-500 text-white px-6 py-2 rounded-lg font-medium text-center">
                        取消
                    </a>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 2: Commit**

```bash
git add templates/subscription.html
git commit -m "feat: rewrite subscription.html with Tailwind form"
```

---

## Task 5: 重写 edit_subscription.html (编辑订阅页)

**Files:**
- Modify: `templates/edit_subscription.html`

- [ ] **Step 1: 重写 edit_subscription.html**

```html
{% extends "base.html" %}

{% block title %}编辑订阅 - VidSpectre{% endblock %}

{% block content %}
<div class="max-w-2xl mx-auto">
    <div class="bg-gray-800 rounded-lg border border-gray-700">
        <div class="px-6 py-4 border-b border-gray-700">
            <h2 class="text-xl font-bold">编辑订阅</h2>
        </div>
        <div class="p-6">
            <form method="POST" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1">名称</label>
                    <input type="text" class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-500" value="{{ subscription.media_name }}" readonly>
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1">类型</label>
                    <input type="text" class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-500" value="{{ '电影' if subscription.media_type == 'movie' else '电视剧' }}" readonly>
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1">当前看到</label>
                    <input type="text" name="current_episode"
                           class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                           value="{{ subscription.current_episode or '' }}"
                           placeholder="例如：第10集">
                </div>

                <div class="flex gap-3 pt-4">
                    <button type="submit"
                            class="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium">
                        保存
                    </button>
                    <a href="{{ url_for('web.index') }}"
                       class="flex-1 bg-gray-600 hover:bg-gray-500 text-white px-6 py-2 rounded-lg font-medium text-center">
                        取消
                    </a>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 2: Commit**

```bash
git add templates/edit_subscription.html
git commit -m "feat: rewrite edit_subscription.html with Tailwind form"
```

---

## Task 6: 重写 settings.html (设置页)

**Files:**
- Modify: `templates/settings.html`

- [ ] **Step 1: 重写 settings.html**

```html
{% extends "base.html" %}

{% block title %}设置 - VidSpectre{% endblock %}

{% block content %}
<div class="max-w-xl mx-auto">
    <div class="bg-gray-800 rounded-lg border border-gray-700">
        <div class="px-6 py-4 border-b border-gray-700">
            <h2 class="text-xl font-bold">全局设置</h2>
        </div>
        <div class="p-6">
            <form method="POST" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1">默认爬取周期 (Cron表达式)</label>
                    <div class="flex gap-2">
                        <select id="preset-select" class="bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white">
                            <option value="">选择预设...</option>
                            <option value="0 * * * *">每小时</option>
                            <option value="0 */6 * * *">每6小时</option>
                            <option value="0 */12 * * *">每12小时</option>
                            <option value="0 9 * * *">每天早上9点</option>
                            <option value="0 9,21 * * *">每天两次</option>
                            <option value="0 9 * * 1,3,5">每周一三五四</option>
                            <option value="custom">自定义</option>
                        </select>
                        <input type="text" name="default_cron"
                               class="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                               value="{{ default_cron }}" placeholder="0 */6 * * *">
                    </div>
                    <p class="text-xs text-gray-500 mt-2">
                        格式说明: 分 小时 日 月 周<br>
                        例: <code class="bg-gray-700 px-1 rounded">0 */6 * * *</code> = 每6小时, <code class="bg-gray-700 px-1 rounded">0 9 * * *</code> = 每天9点
                    </p>
                </div>

                <div class="flex gap-3 pt-4">
                    <button type="submit"
                            class="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium">
                        保存
                    </button>
                    <a href="{{ url_for('web.index') }}"
                       class="flex-1 bg-gray-600 hover:bg-gray-500 text-white px-6 py-2 rounded-lg font-medium text-center">
                        返回
                    </a>
                </div>
            </form>
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

- [ ] **Step 2: Commit**

```bash
git add templates/settings.html
git commit -m "feat: rewrite settings.html with Tailwind form"
```

---

## Task 7: 修复隐藏字段 CSS

**Files:**
- Modify: `templates/base.html`

- [ ] **Step 1: 添加 hidden utility class 支持**

Tailwind 的 `hidden` 在深色模式下可能有问题，添加自定义 CSS：

```html
<!-- Add before </head> in base.html -->
<style>
    .hidden { display: none !important; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add templates/base.html
git commit -m "fix: add hidden utility CSS for Tailwind dark mode"
```

---

## Task 8: 验证所有功能

**验证步骤:**

1. 启动开发服务器
```bash
cd /Users/jasper/Documents/Code/VidSpectre && uv run python run.py
```

2. 测试以下功能:
- [ ] 访问 http://localhost:5002 订阅列表显示正常
- [ ] 点击「展开」按钮能展开剧集列表
- [ ] 点击「获取」按钮能获取磁力链接
- [ ] 点击「爬取」按钮能触发爬取
- [ ] 点击「更多」菜单能展开保存/编辑/删除选项
- [ ] 点击「保存」按钮能保存订阅信息
- [ ] 添加订阅页面搜索功能正常
- [ ] 编辑订阅页面正常显示和保存
- [ ] 设置页面预设联动正常
- [ ] 移动端布局正常显示

3. 移动端测试 (浏览器 DevTools)
- [ ] 卡片全宽显示
- [ ] 按钮触摸目标足够大 (至少 44px)
- [ ] 展开列表单列显示

---

## 功能对照表

| 功能 | 状态 |
|------|------|
| 显示订阅列表 | ✅ 已实现 |
| 添加订阅 | ✅ 已实现 |
| 编辑订阅 | ✅ 已实现 |
| 爬取订阅 | ✅ 已实现 |
| 保存订阅 | ✅ 已实现 |
| 删除订阅 | ✅ 已实现 |
| 展开剧集列表 | ✅ 已实现 |
| 获取磁力链接 | ✅ 已实现 |
| 周期选择器 | ✅ 已实现 |
| 全局设置 | ✅ 已实现 |
| 深色主题 | ✅ 已实现 |
| 移动端响应式 | ✅ 已实现 |

## 风险与注意事项

1. **Bootstrap 完全移除** — 确认没有任何第三方依赖依赖 Bootstrap
2. **JS 选择器匹配** — 确保 app.js 中的选择器与 Tailwind 生成的 class 匹配
3. **深色模式覆盖** — 确保所有元素在深色模式下正常显示
4. **API 兼容性** — 所有 API 接口不变，只改前端
