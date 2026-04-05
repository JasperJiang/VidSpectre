# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

```bash
cd /Users/jasper/Documents/Code/VidSpectre
uv run python run.py
```

The app runs on port 5002 by default. If port 5002 is in use (common with AirPlay on macOS), Flask will report an alternative port.

## Commands

- **Run dev server**: `uv run python run.py [--port PORT]` (default port 5002, uses Flask debug mode)
- **Production server**: `uv run gunicorn -w 4 -b 0.0.0.0:5002 run:app`
- **Docker**: `docker build -t vidspectre . && docker run -d -p 5002:5002 -v ./storage:/app/storage --name vidspectre vidspectre`
- **Docker Compose**: `docker-compose up --build`

## Architecture

### Plugin System
VidSpectre uses a plugin architecture for data sources. Plugins are loaded from `plugins/sources/`:
- Plugins implement `DataSourcePlugin` interface (see `plugins/interfaces.py`)
- The `plugins/registry.py` maintains a registry of loaded plugins
- Currently implemented: `btbtla` plugin for btbtla.com

### Scheduler
- APScheduler runs on a global cron schedule defined by `DEFAULT_INTERVAL_CRON` in `config.py`
- Default: `"0 */6 * * *"` (every 6 hours)
- All active subscriptions are crawled together at each scheduled time
- Network errors retry up to `FETCH_RETRY_COUNT` times (default: 3)

### Database Models
- `Subscription` model in `app/database/models.py`
- Key fields: `media_type`, `media_name`, `media_id`, `source_plugin`, `current_episode`, `search_keywords`
- `Setting` model (key-value) for persisting app settings like `default_interval_cron` and `fetch_retry_count`

### API Structure
- REST API via Flask Blueprints in `app/api/routes.py`
- Web UI via Blueprints in `app/web/routes.py`
- API endpoints prefixed with `/api/`
- `POST /api/fetch-all` - Trigger crawl for all subscriptions (returns task_id)
- `GET /api/fetch-all/<task_id>` - Poll task status
- `GET /api/subscriptions/<id>/episodes` - Get TV episode list (grouped by episode number)
- `GET /api/subscriptions/<id>/movie-links` - Get movie download resources (direct list, no episode grouping)

### Frontend
- Tailwind CSS v3 (Play CDN) + Vanilla JS
- Mobile-first responsive design with dark theme
- JavaScript extracted to `static/js/app.js` using addEventListener
- Card layout (not table) for subscription list
- Templates use Jinja2 inheritance

## Cron Schedule Feature
- Global cron expression in `config.Config.DEFAULT_INTERVAL_CRON` ("0 */6 * * *" = every 6 hours)
- Retry count configurable via `config.Config.FETCH_RETRY_COUNT` (default: 3)
- Settings page at `/settings` for configuring global default and retry count
- Manual trigger button on settings page triggers crawl immediately (polling for status)

## Critical Implementation Details

### Flask App Factory Pattern
The app uses Flask's application factory pattern in `app/__init__.py`:
- Blueprints (`api_bp`, `web_bp`) are defined in `app/api/__init__.py` and `app/web/__init__.py`
- Templates are in `../templates` (project root, not `app/templates`)
- Static files are in `../static` (project root)

### btbtla Plugin URL Patterns
- Detail page: `https://www.btbtla.com/detail/{media_id}.html`
- Download/tdown page: `https://www.btbtla.com/tdown/{resource_id}.html`
- **Important**: `media_id` (e.g., `47001256.html`) is NOT the same as resource ID
- Resources are parsed directly from the detail page (no separate tdown API call needed)
- Magnet links are only available on the tdown page
- **Movie vs TV behavior**: TV shows group resources by episode number; movies show a flat list of resources directly

### media_id is Critical
- The `Subscription.media_id` field MUST be set for both episode listing (TV) and resource listing (movies) to work
- If `media_id` is `None`, the "展开" button will show a ⚠ warning
- When adding subscriptions via search, ensure `media_id` is properly saved

### Template Files
Templates are in `../templates` (project root):
- `index.html` - Subscription list page
- `subscription.html` - Add subscription page (with search)
- `edit_subscription.html` - Edit subscription page
- `settings.html` - Global settings page
- `base.html` - Base template with shared layout and JS

### Database
- SQLite database at `storage/vidspectre.db`
- This file is gitignored and should NOT be committed
