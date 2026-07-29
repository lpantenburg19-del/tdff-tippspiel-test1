import os
from datetime import timedelta

from flask import Flask

from config import Config
from .db import db
from .seed import seed_stages


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    app.permanent_session_lifetime = timedelta(days=30)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    from .routes.player import bp as player_bp
    from .routes.admin import bp as admin_bp

    app.register_blueprint(player_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()
        seed_stages()

    return app
