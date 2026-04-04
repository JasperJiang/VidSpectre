# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

```bash
cd /Users/jasper/Documents/Code/VidSpectre
uv run python run.py
```

The app runs on port 5002 by default. If port 5002 is in use (common with AirPlay on macOS), Flask will report an alternative port.

## Commands

- **Run dev server**: `uv run python run.py` (uses Flask debug mode)
- **Production server**: `uv run gunicorn -w 4 -b 0.0.0.0:5002 run:app`

## Architecture

### Plugin System
VidSpectre uses a plugin architecture for data sources. Plugins are loaded from `plugins/sources/`:
- Plugins implement `DataSourcePlugin` interface (see `plugins/interfaces.py`)
- The `plugins/registry.py` maintains a registry of loaded plugins
- Currently implemented: `btbtla` plugin for btbtla.com

### Scheduler
- APScheduler runs hourly to check subscriptions
- Each subscription can have a custom `interval_cron` (cron expression)
- Fallback: `DEFAULT_INTERVAL_CRON` from `config.py` ("0 */6 * * *" = every 6 hours)
- Uses `croniter` library to evaluate cron expressions

### Database Models
- `Subscription` model in `app/database/models.py`
- Key fields: `media_type`, `media_name`, `media_id`, `source_plugin`, `current_episode`, `search_keywords`, `interval_cron`

### API Structure
- REST API via Flask Blueprints in `app/api/routes.py`
- Web UI via Blueprints in `app/web/routes.py`
- API endpoints prefixed with `/api/`

### Frontend
- Bootstrap 5 + Vanilla JS
- Global JS functions in `templates/base.html` (inline onclick handlers, not addEventListener in DOMContentLoaded)
- Templates use Jinja2 inheritance

## Cron Schedule Feature
- Per-subscription cron expressions stored in `Subscription.interval_cron`
- Global default in `config.Config.DEFAULT_INTERVAL_CRON`
- Settings page at `/settings` for configuring global default
