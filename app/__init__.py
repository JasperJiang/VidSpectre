from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__,
                template_folder="../templates",
                static_folder="../static")
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
        # Load persisted settings
        from app.database.models import Setting
        cron_setting = Setting.query.get("default_interval_cron")
        if cron_setting:
            Config.DEFAULT_INTERVAL_CRON = cron_setting.value

        scheduler_enabled = Setting.query.get("scheduler_enabled")
        if scheduler_enabled:
            Config.SCHEDULER_ENABLED = scheduler_enabled.value == "true"

    # Setup scheduler
    from app.scheduler.tasks import setup_scheduler
    setup_scheduler(app)

    return app