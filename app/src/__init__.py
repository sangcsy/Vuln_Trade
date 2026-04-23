import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from .db import close_db, initialize_runtime_schema
from .routes.admin import admin_bp
from .routes.auth import auth_bp
from .routes.community import community_bp
from .routes.main import main_bp
from .routes.stocks import stocks_bp
from .routes.wallet import wallet_bp


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.teardown_appcontext(close_db)
    try:
        initialize_runtime_schema(app)
    except Exception:
        pass

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(stocks_bp, url_prefix="/stocks")
    app.register_blueprint(wallet_bp, url_prefix="/wallet")
    app.register_blueprint(community_bp, url_prefix="/community")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    return app
