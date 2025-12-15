from flask import Flask, render_template
from .config import Config
from .extensions import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from .routes.certificates import bp as cert_bp
    from .routes.assets import bp as assets_bp
    from .routes.sync import bp as sync_bp
    from .routes.api import bp as api_bp   
    from .routes.home import bp as home_bp

    app.register_blueprint(cert_bp)
    app.register_blueprint(assets_bp)
    app.register_blueprint(sync_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(home_bp)     

    with app.app_context():
        db.create_all()

    return app
