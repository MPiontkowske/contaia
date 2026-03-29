from .auth import auth_bp
from .main import main_bp
from .tools import tools_bp
from .api import api_bp
from .admin import admin_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
