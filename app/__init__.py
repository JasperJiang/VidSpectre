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