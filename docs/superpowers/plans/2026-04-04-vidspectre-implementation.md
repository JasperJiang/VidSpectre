# VidSpectre Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个影视订阅爬取应用，支持插件式数据源和通知系统，Web管理界面

**Architecture:** 采用插件式架构，核心系统与具体实现解耦。通过Flask提供REST API和Web界面，使用APScheduler实现定时任务，SQLite存储订阅数据。

**Tech Stack:** Python 3.x + Flask + SQLite + APScheduler + Bootstrap 5

---

## 文件结构

```
vid spectre/
├── app/
│   ├── __init__.py          # Flask应用工厂
│   ├── api/                 # REST API蓝图
│   │   └── routes.py         # API路由
│   ├── web/                 # Web界面蓝图
│   │   └── routes.py        # Web路由
│   ├── core/                # 核心逻辑
│   │   ├── subscription.py  # 订阅管理
│   │   └── checker.py        # 更新检查
│   ├── scheduler/           # 定时任务
│   │   └── tasks.py         # 定时任务实现
│   └── database/            # 数据库
│       ├── models.py        # SQLAlchemy模型
│       └── migrations.py    # 数据库初始化
├── plugins/                 # 插件系统
│   ├── __init__.py
│   ├── loader.py            # 插件加载器
│   ├── registry.py          # 插件注册表
│   ├── interfaces.py        # 插件接口定义
│   └── sources/             # 数据源插件
│       ├── __init__.py
│       └── btbtla/          # btbtla插件
│           ├── __init__.py
│           ├── plugin.py    # 插件实现
│           └── parser.py    # 页面解析
├── storage/                 # SQLite数据库目录
├── static/                  # 静态资源
│   ├── css/
│   └── js/
├── templates/               # HTML模板
│   ├── base.html
│   ├── index.html
│   └── subscription.html
├── config.py                # 配置
├── requirements.txt         # 依赖
└── run.py                   # 启动文件
```

---

### Task 1: Project Setup - 初始化项目结构和依赖

**Files:**
- Create: `requirements.txt`
- Create: `config.py`
- Create: `run.py`

- [ ] **Step 1: Create requirements.txt**

```txt
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
APScheduler==3.10.4
requests==2.31.0
beautifulsoup4==4.12.2
lxml==4.9.3
gunicorn==21.2.0
```

- [ ] **Step 2: Create config.py**

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{STORAGE_DIR / 'vidspectre.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Scheduler settings
    SCHEDULER_INTERVAL_HOURS = 6

    # Plugin settings
    PLUGIN_DIR = BASE_DIR / "plugins" / "sources"
```

- [ ] **Step 3: Create run.py**

```python
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

- [ ] **Step 4: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: Install all packages successfully

- [ ] **Step 5: Commit**

```bash
git add requirements.txt config.py run.py
git commit -m "chore: add project setup files"
```
---

### Task 2: Database Models - 创建数据库模型

**Files:**
- Create: `app/database/models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models.py
import sys
sys.path.insert(0, "/Users/jasper/Documents/Code/VidSpectre")

def test_subscription_model_exists():
    from app.database.models import Subscription
    assert Subscription is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_models.py -v`
Expected: FAIL - no module 'app.database.models'

- [ ] **Step 3: Create app/__init__.py (empty first)**

```python
# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")
    db.init_app(app)
    return app
```

- [ ] **Step 4: Create app/database/models.py**

```python
# app/database/models.py
from datetime import datetime
from app import db

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    media_type = db.Column(db.String(20), nullable=False)  # 'movie' or 'tv'
    media_name = db.Column(db.String(200), nullable=False)
    media_id = db.Column(db.String(100))  # Source-specific ID
    source_plugin = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default="active")  # active, paused
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Latest update info
    latest_episode = db.Column(db.String(50))
    latest_update_time = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "media_type": self.media_type,
            "media_name": self.media_name,
            "media_id": self.media_id,
            "source_plugin": self.source_plugin,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "latest_episode": self.latest_episode,
            "latest_update_time": self.latest_update_time.isoformat() if self.latest_update_time else None,
        }
```

- [ ] **Step 5: Update app/__init__.py to import models**

```python
# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")
    db.init_app(app)

    # Import models to register them
    from app.database import models
    with app.app_context():
        db.create_all()

    return app
```

- [ ] **Step 6: Create app/database/__init__.py**

```python
# app/database/__init__.py
# Database package
```

- [ ] **Step 7: Run test to verify models work**

Run: `python -c "from app import create_app; app = create_app(); print('Database initialized')"`
Expected: Output "Database initialized"

- [ ] **Step 8: Commit**

```bash
git add app/ config.py run.py
git commit -m "feat: add database models and Flask app setup"
```
---

### Task 3: Plugin System - 插件系统核心

**Files:**
- Create: `plugins/interfaces.py`
- Create: `plugins/loader.py`
- Create: `plugins/registry.py`
- Create: `plugins/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_plugin_system.py
def test_plugin_interfaces_exist():
    from plugins.interfaces import DataSourcePlugin, NotifierPlugin
    assert DataSourcePlugin is not None
    assert NotifierPlugin is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_plugin_system.py -v`
Expected: FAIL - no module 'plugins'

- [ ] **Step 3: Create plugins/__init__.py**

```python
# plugins/__init__.py
"""Plugin system for VidSpectre"""
```

- [ ] **Step 4: Create plugins/interfaces.py**

```python
# plugins/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from enum import Enum

class MediaType(Enum):
    MOVIE = "movie"
    TV = "tv"

class MediaItem:
    def __init__(self, media_id: str, name: str, media_type: MediaType,
                 cover_url: Optional[str] = None, detail_url: Optional[str] = None):
        self.media_id = media_id
        self.name = name
        self.media_type = media_type
        self.cover_url = cover_url
        self.detail_url = detail_url

    def to_dict(self) -> Dict[str, Any]:
        return {
            "media_id": self.media_id,
            "name": self.name,
            "media_type": self.media_type.value,
            "cover_url": self.cover_url,
            "detail_url": self.detail_url,
        }

class UpdateInfo:
    def __init__(self, media_id: str, latest_episode: str, update_time: Optional[str] = None,
                 download_links: Optional[List[Dict]] = None):
        self.media_id = media_id
        self.latest_episode = latest_episode
        self.update_time = update_time
        self.download_links = download_links or []

class DataSourcePlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name"""
        pass

    @property
    @abstractmethod
    def supported_media_types(self) -> List[MediaType]:
        """Supported media types"""
        pass

    @abstractmethod
    async def search(self, keyword: str) -> List[MediaItem]:
        """Search for media"""
        pass

    @abstractmethod
    async def get_updates(self, media_id: str) -> Optional[UpdateInfo]:
        """Get latest update info for a media"""
        pass

    @abstractmethod
    async def get_download_links(self, media_id: str) -> List[Dict]:
        """Get download links"""
        pass

class NotifierPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name"""
        pass

    @abstractmethod
    async def send(self, title: str, message: str, **kwargs) -> bool:
        """Send notification"""
        pass
```

- [ ] **Step 5: Create plugins/registry.py**

```python
# plugins/registry.py
from typing import Dict, List, Optional
from plugins.interfaces import DataSourcePlugin, NotifierPlugin

class PluginRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data_sources: Dict[str, DataSourcePlugin] = {}
            cls._instance._notifiers: Dict[str, NotifierPlugin] = {}
        return cls._instance

    def register_data_source(self, plugin: DataSourcePlugin):
        self._data_sources[plugin.name] = plugin

    def register_notifier(self, plugin: NotifierPlugin):
        self._notifiers[plugin.name] = plugin

    def get_data_source(self, name: str) -> Optional[DataSourcePlugin]:
        return self._data_sources.get(name)

    def get_notifier(self, name: str) -> Optional[NotifierPlugin]:
        return self._notifiers.get(name)

    def list_data_sources(self) -> List[str]:
        return list(self._data_sources.keys())

    def list_notifiers(self) -> List[str]:
        return list(self._notifiers.keys())

registry = PluginRegistry()
```

- [ ] **Step 6: Create plugins/loader.py**

```python
# plugins/loader.py
import importlib
import pkgutil
from pathlib import Path
from typing import List
from plugins.interfaces import DataSourcePlugin, NotifierPlugin
from plugins.registry import registry

def discover_plugins(plugin_dir: Path) -> List[str]:
    """Discover available plugin directories"""
    plugins = []
    if not plugin_dir.exists():
        return plugins
    for item in plugin_dir.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            plugins.append(item.name)
    return plugins

def load_plugins(plugin_dir: Path):
    """Load all plugins from plugin directory"""
    plugin_names = discover_plugins(plugin_dir)

    for name in plugin_names:
        try:
            module = importlib.import_module(f"plugins.sources.{name}.plugin")
            if hasattr(module, "register"):
                module.register(registry)
                print(f"Loaded plugin: {name}")
        except Exception as e:
            print(f"Failed to load plugin {name}: {e}")
```

- [ ] **Step 7: Run test to verify interfaces work**

Run: `python -c "from plugins.interfaces import DataSourcePlugin, NotifierPlugin; print('OK')"`
Expected: Output "OK"

- [ ] **Step 8: Commit**

```bash
git add plugins/
git commit -m "feat: add plugin system core interfaces and loader"
```
---

### Task 4: BTBTLA Data Source Plugin - btbtla数据源插件实现

**Files:**
- Create: `plugins/sources/__init__.py`
- Create: `plugins/sources/btbtla/__init__.py`
- Create: `plugins/sources/btbtla/plugin.py`
- Create: `plugins/sources/btbtla/parser.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_btbtla_plugin.py
def test_btbtla_plugin_loads():
    from plugins.sources.btbtla.plugin import BtbtlaPlugin
    plugin = BtbtlaPlugin()
    assert plugin.name == "btbtla"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_btbtla_plugin.py -v`
Expected: FAIL - no module 'plugins.sources.btbtla'

- [ ] **Step 3: Create plugins/sources/__init__.py**

```python
# plugins/sources/__init__.py
"""Data source plugins"""
```

- [ ] **Step 4: Create plugins/sources/btbtla/__init__.py**

```python
# plugins/sources/btbtla/__init__.py
"""BTBTLA data source plugin"""
```

- [ ] **Step 5: Create plugins/sources/btbtla/parser.py**

```python
# plugins/sources/btbtla/parser.py
import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Dict
from plugins.interfaces import MediaItem, MediaType, UpdateInfo

BASE_URL = "https://www.btbtla.com"

class BtbtlaParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })

    def search(self, keyword: str) -> List[MediaItem]:
        """Search for media"""
        url = f"{BASE_URL}/search"
        params = {"keyword": keyword}

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return self._parse_search_results(response.text)
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def _parse_search_results(self, html: str) -> List[MediaItem]:
        """Parse search results"""
        items = []
        soup = BeautifulSoup(html, "lxml")

        # Find media items - adjust selector based on actual page structure
        for item in soup.select(".movie-item, .video-item, .item"):
            try:
                title_elem = item.select_one("a.title, .title a, h3 a")
                if not title_elem:
                    continue

                name = title_elem.get_text(strip=True)
                detail_url = title_elem.get("href", "")

                # Extract media ID from URL
                media_id = self._extract_media_id(detail_url)
                if not media_id:
                    continue

                # Get cover image
                img_elem = item.select_one("img")
                cover_url = img_elem.get("src") if img_elem else None

                # Determine media type
                media_type = MediaType.TV if "/tv/" in detail_url else MediaType.MOVIE

                items.append(MediaItem(
                    media_id=media_id,
                    name=name,
                    media_type=media_type,
                    cover_url=cover_url,
                    detail_url=detail_url
                ))
            except Exception as e:
                continue

        return items

    def _extract_media_id(self, url: str) -> Optional[str]:
        """Extract media ID from URL"""
        if not url:
            return None
        # Extract ID from URL pattern like /detail/12345 or /movie/12345
        parts = url.strip("/").split("/")
        if parts:
            return parts[-1]
        return None

    def get_updates(self, media_id: str) -> Optional[UpdateInfo]:
        """Get update info for media"""
        url = f"{BASE_URL}/detail/{media_id}"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return self._parse_detail_page(response.text, media_id)
        except Exception as e:
            print(f"Get updates error: {e}")
            return None

    def _parse_detail_page(self, html: str, media_id: str) -> Optional[UpdateInfo]:
        """Parse detail page"""
        soup = BeautifulSoup(html, "lxml")

        # Get latest episode/title
        latest_episode = ""
        episode_elem = soup.select_one(".latest-episode, .episode, .update-title")
        if episode_elem:
            latest_episode = episode_elem.get_text(strip=True)

        # Get update time
        update_time = None
        time_elem = soup.select_one(".time, .date, time")
        if time_elem:
            update_time = time_elem.get_text(strip=True)

        # Get download links
        download_links = []
        for link_elem in soup.select(".download-link, .magnet-link, a[href^='magnet:']"):
            href = link_elem.get("href", "")
            if href.startswith("magnet:") or href.endswith(".torrent"):
                download_links.append({
                    "type": "magnet" if href.startswith("magnet") else "torrent",
                    "url": href,
                    "title": link_elem.get_text(strip=True)
                })

        return UpdateInfo(
            media_id=media_id,
            latest_episode=latest_episode,
            update_time=update_time,
            download_links=download_links
        )

    def get_download_links(self, media_id: str) -> List[Dict]:
        """Get download links"""
        update_info = self.get_updates(media_id)
        return update_info.download_links if update_info else []
```

- [ ] **Step 6: Create plugins/sources/btbtla/plugin.py**

```python
# plugins/sources/btbtla/plugin.py
import asyncio
from typing import List, Optional, Dict
from plugins.interfaces import DataSourcePlugin, MediaType, MediaItem, UpdateInfo
from plugins.sources.btbtla.parser import BtbtlaParser

class BtbtlaPlugin(DataSourcePlugin):
    def __init__(self):
        self.parser = BtbtlaParser()

    @property
    def name(self) -> str:
        return "btbtla"

    @property
    def supported_media_types(self) -> List[MediaType]:
        return [MediaType.MOVIE, MediaType.TV]

    async def search(self, keyword: str) -> List[MediaItem]:
        """Search for media"""
        # Run sync parser in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.parser.search, keyword)

    async def get_updates(self, media_id: str) -> Optional[UpdateInfo]:
        """Get latest update info"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.parser.get_updates, media_id)

    async def get_download_links(self, media_id: str) -> List[Dict]:
        """Get download links"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.parser.get_download_links, media_id)

def register(registry):
    """Register plugin to registry"""
    registry.register_data_source(BtbtlaPlugin())
```

- [ ] **Step 7: Run test to verify plugin loads**

Run: `python -c "from plugins.sources.btbtla.plugin import BtbtlaPlugin; p = BtbtlaPlugin(); print(p.name)"`
Expected: Output "btbtla"

- [ ] **Step 8: Commit**

```bash
git add plugins/sources/
git commit -m "feat: add btbtla data source plugin"
```
---

### Task 5: Core API - REST API实现

**Files:**
- Create: `app/api/__init__.py`
- Create: `app/api/routes.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_api.py
def test_api_subscription_list():
    from app import create_app
    app = create_app()
    with app.test_client() as client:
        response = client.get("/api/subscriptions")
        assert response.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_api.py -v`
Expected: FAIL - no module 'app.api'

- [ ] **Step 3: Create app/api/__init__.py**

```python
# app/api/__init__.py
from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

from app.api import routes
```

- [ ] **Step 4: Create app/api/routes.py**

```python
# app/api/routes.py
from flask import jsonify, request
from app.api import api_bp
from app import db
from app.database.models import Subscription
from plugins.registry import registry
import asyncio

@api_bp.route("/subscriptions", methods=["GET"])
def list_subscriptions():
    """List all subscriptions"""
    subscriptions = Subscription.query.all()
    return jsonify([s.to_dict() for s in subscriptions])

@api_bp.route("/subscriptions", methods=["POST"])
def add_subscription():
    """Add a new subscription"""
    data = request.json

    media_type = data.get("media_type")
    media_name = data.get("media_name")
    media_id = data.get("media_id")
    source_plugin = data.get("source_plugin", "btbtla")

    if not all([media_type, media_name]):
        return jsonify({"error": "media_type and media_name are required"}), 400

    subscription = Subscription(
        media_type=media_type,
        media_name=media_name,
        media_id=media_id,
        source_plugin=source_plugin
    )
    db.session.add(subscription)
    db.session.commit()

    return jsonify(subscription.to_dict()), 201

@api_bp.route("/subscriptions/<int:sub_id>", methods=["DELETE"])
def delete_subscription(sub_id):
    """Delete a subscription"""
    subscription = Subscription.query.get_or_404(sub_id)
    db.session.delete(subscription)
    db.session.commit()
    return "", 204

@api_bp.route("/search", methods=["GET"])
def search_media():
    """Search media from data source"""
    keyword = request.args.get("q", "")
    source = request.args.get("source", "btbtla")

    if not keyword:
        return jsonify({"error": "keyword is required"}), 400

    plugin = registry.get_data_source(source)
    if not plugin:
        return jsonify({"error": f"Source plugin '{source}' not found"}), 404

    # Run async search
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        results = loop.run_until_complete(plugin.search(keyword))
    finally:
        loop.close()

    return jsonify([item.to_dict() for item in results])

@api_bp.route("/plugins", methods=["GET"])
def list_plugins():
    """List available plugins"""
    return jsonify({
        "data_sources": registry.list_data_sources(),
        "notifiers": registry.list_notifiers()
    })
```

- [ ] **Step 5: Update app/__init__.py to register blueprint**

```python
# app/__init__.py (update)
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")
    db.init_app(app)

    # Import models to register them
    from app.database import models

    # Load plugins
    from plugins.loader import load_plugins
    from config import Config
    load_plugins(Config.PLUGIN_DIR)

    # Register blueprints
    from app.api import api_bp
    from app.web import web_bp
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)

    with app.app_context():
        db.create_all()

    return app
```

- [ ] **Step 6: Run test to verify API works**

Run: `python -c "from app import create_app; app = create_app(); print('App created')"`
Expected: Output "App created"

- [ ] **Step 7: Commit**

```bash
git add app/api/
git commit -m "feat: add REST API for subscription management"
```
---

### Task 6: Web UI - Web管理界面

**Files:**
- Create: `app/web/__init__.py`
- Create: `app/web/routes.py`
- Create: `templates/base.html`
- Create: `templates/index.html`
- Create: `templates/subscription.html`
- Create: `static/css/main.css`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_web.py
def test_web_index():
    from app import create_app
    app = create_app()
    with app.test_client() as client:
        response = client.get("/")
        assert response.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_web.py -v`
Expected: FAIL - no module 'app.web'

- [ ] **Step 3: Create app/web/__init__.py**

```python
# app/web/__init__.py
from flask import Blueprint

web_bp = Blueprint("web", __name__)

from app.web import routes
```

- [ ] **Step 4: Create app/web/routes.py**

```python
# app/web/routes.py
from flask import render_template, jsonify, request, redirect, url_for
from app.web import web_bp
from app import db
from app.database.models import Subscription

@web_bp.route("/")
def index():
    """Home page - subscription list"""
    subscriptions = Subscription.query.all()
    return render_template("index.html", subscriptions=subscriptions)

@web_bp.route("/subscription/add", methods=["GET", "POST"])
def add_subscription():
    """Add subscription page"""
    if request.method == "POST":
        media_type = request.form.get("media_type")
        media_name = request.form.get("media_name")
        media_id = request.form.get("media_id")
        source_plugin = request.form.get("source_plugin", "btbtla")

        subscription = Subscription(
            media_type=media_type,
            media_name=media_name,
            media_id=media_id,
            source_plugin=source_plugin
        )
        db.session.add(subscription)
        db.session.commit()
        return redirect(url_for("web.index"))

    return render_template("subscription.html", action="add")

@web_bp.route("/subscription/<int:sub_id>/delete", methods=["POST"])
def delete_subscription(sub_id):
    """Delete subscription"""
    subscription = Subscription.query.get_or_404(sub_id)
    db.session.delete(subscription)
    db.session.commit()
    return redirect(url_for("web.index"))
```

- [ ] **Step 5: Create templates/base.html**

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}VidSpectre{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('web.index') }}">VidSpectre</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('web.index') }}">订阅列表</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('web.add_subscription') }}">添加订阅</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <main class="container my-4">
        {% block content %}{% endblock %}
    </main>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

- [ ] **Step 6: Create templates/index.html**

```html
<!-- templates/index.html -->
{% extends "base.html" %}

{% block title %}订阅列表 - VidSpectre{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>我的订阅</h1>
            <a href="{{ url_for('web.add_subscription') }}" class="btn btn-primary">添加订阅</a>
        </div>

        {% if subscriptions %}
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>类型</th>
                        <th>名称</th>
                        <th>数据源</th>
                        <th>最新更新</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    {% for sub in subscriptions %}
                    <tr>
                        <td>
                            {% if sub.media_type == 'movie' %}
                            <span class="badge bg-primary">电影</span>
                            {% else %}
                            <span class="badge bg-success">电视剧</span>
                            {% endif %}
                        </td>
                        <td>{{ sub.media_name }}</td>
                        <td>{{ sub.source_plugin }}</td>
                        <td>{{ sub.latest_episode or '-' }}</td>
                        <td>
                            <form action="{{ url_for('web.delete_subscription', sub_id=sub.id) }}" method="POST" style="display:inline;">
                                <button type="submit" class="btn btn-sm btn-danger" onclick="return confirm('确定删除?')">删除</button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% else %}
        <div class="alert alert-info">
            暂无订阅，<a href="{{ url_for('web.add_subscription') }}">点击添加</a>
        </div>
        {% endif %}
    </div>
</div>
{% endblock %}
```

- [ ] **Step 7: Create templates/subscription.html**

```html
<!-- templates/subscription.html -->
{% extends "base.html" %}

{% block title %}添加订阅 - VidSpectre{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h4>添加订阅</h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">媒体类型</label>
                        <select name="media_type" class="form-select" required>
                            <option value="movie">电影</option>
                            <option value="tv">电视剧</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">名称</label>
                        <input type="text" name="media_name" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">数据源 (可选)</label>
                        <input type="text" name="source_plugin" class="form-control" value="btbtla" readonly>
                    </div>
                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-primary">添加</button>
                        <a href="{{ url_for('web.index') }}" class="btn btn-secondary">取消</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 8: Create static/css/main.css**

```css
/* static/css/main.css */
body {
    min-height: 100vh;
    background-color: #f8f9fa;
}

.navbar-brand {
    font-weight: bold;
}

.table th {
    background-color: #f8f9fa;
}

.badge {
    font-size: 0.85em;
}
```

- [ ] **Step 9: Run test to verify web works**

Run: `python -c "from app import create_app; app = create_app(); print('Web routes registered')"`
Expected: Output "Web routes registered"

- [ ] **Step 10: Commit**

```bash
git add app/web/ templates/ static/
git commit -m "feat: add web UI for subscription management"
```
---

### Task 7: Scheduler - 定时任务实现

**Files:**
- Create: `app/scheduler/__init__.py`
- Create: `app/scheduler/tasks.py`
- Create: `app/core/checker.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scheduler.py
def test_scheduler_imports():
    from app.scheduler.tasks import scheduler
    assert scheduler is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_scheduler.py -v`
Expected: FAIL - no module 'app.scheduler'

- [ ] **Step 3: Create app/scheduler/__init__.py**

```python
# app/scheduler/__init__.py
"""Scheduler package"""
```

- [ ] **Step 4: Create app/core/checker.py**

```python
# app/core/checker.py
"""Update checker - check subscriptions for updates"""
import asyncio
from datetime import datetime
from app import db
from app.database.models import Subscription
from plugins.registry import registry

async def check_subscription(subscription: Subscription):
    """Check a single subscription for updates"""
    plugin = registry.get_data_source(subscription.source_plugin)
    if not plugin:
        return None

    try:
        update_info = await plugin.get_updates(subscription.media_id)
        return update_info
    except Exception as e:
        print(f"Error checking {subscription.media_name}: {e}")
        return None

async def check_all_subscriptions():
    """Check all active subscriptions for updates"""
    subscriptions = Subscription.query.filter_by(status="active").all()
    results = []

    for sub in subscriptions:
        update_info = await check_subscription(sub)
        if update_info:
            # Check if there's a new episode
            if subscription.latest_episode != update_info.latest_episode:
                sub.latest_episode = update_info.latest_episode
                sub.latest_update_time = datetime.utcnow()
                db.session.commit()

                results.append({
                    "subscription": sub,
                    "update_info": update_info
                })

    return results

def run_check():
    """Run check in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(check_all_subscriptions())
    finally:
        loop.close()
```

- [ ] **Step 5: Create app/scheduler/tasks.py**

```python
# app/scheduler/tasks.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config import Config

scheduler = BackgroundScheduler()

def setup_scheduler(app):
    """Setup scheduler with app context"""
    from app.core.checker import run_check

    scheduler.add_job(
        func=lambda: with_app_context(app, run_check),
        trigger=IntervalTrigger(hours=Config.SCHEDULER_INTERVAL_HOURS),
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

- [ ] **Step 6: Update app/__init__.py to init scheduler**

```python
# app/__init__.py (update)
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")
    db.init_app(app)

    # Import models to register them
    from app.database import models

    # Load plugins
    from plugins.loader import load_plugins
    from config import Config
    load_plugins(Config.PLUGIN_DIR)

    # Register blueprints
    from app.api import api_bp
    from app.web import web_bp
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)

    with app.app_context():
        db.create_all()

    # Setup scheduler
    from app.scheduler.tasks import setup_scheduler
    setup_scheduler(app)

    return app
```

- [ ] **Step 7: Run test to verify scheduler works**

Run: `python -c "from app import create_app; app = create_app(); from app.scheduler.tasks import scheduler; print('Scheduler ready')"`
Expected: Output "Scheduler ready"

- [ ] **Step 8: Commit**

```bash
git add app/scheduler/ app/core/
git commit -m "feat: add scheduler for automatic update checking"
```
---

### Task 8: Core Package - 核心逻辑包初始化

**Files:**
- Create: `app/core/__init__.py`

- [ ] **Step 1: Create app/core/__init__.py**

```python
# app/core/__init__.py
"""Core functionality - subscription management, update checking"""
```

- [ ] **Step 2: Commit**

```bash
git add app/core/
git commit -m "chore: add core package init"
```

---

## 总结

完成以上8个任务后，你将拥有:
- ✅ Flask Web应用基础结构
- ✅ SQLite数据库 + SQLAlchemy模型
- ✅ 插件系统（接口定义、加载器、注册表）
- ✅ btbtla数据源插件实现
- ✅ REST API（订阅管理、搜索、插件列表）
- ✅ Web管理界面（Bootstrap 5）
- ✅ APScheduler定时任务

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-04-vidspectre-implementation.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**