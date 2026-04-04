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

    # Setup scheduler
    from app.scheduler.tasks import setup_scheduler
    setup_scheduler(app)

    return app