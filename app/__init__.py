import os
import logging
from flask import Flask
from .config import config_map
from .extensions import db, limiter, mail


def _init_sentry(dsn: str | None) -> None:
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(
            dsn=dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.1,
        )
    except Exception as e:
        logging.getLogger(__name__).warning("Sentry não inicializado: %s", e)


def create_app(env: str | None = None) -> Flask:
    if env is None:
        env = os.environ.get("FLASK_ENV", "production")

    cfg_class = config_map.get(env, config_map["default"])

    _init_sentry(os.environ.get("SENTRY_DSN"))

    if env == "production":
        try:
            cfg_class.validate()
        except AttributeError:
            pass  # DevelopmentConfig não tem validate()

    app = Flask(__name__, template_folder="templates")
    app.config.from_object(cfg_class)

    _configure_logging(app)
    _configure_security_headers(app)

    db.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)

    from .routes import register_blueprints
    register_blueprints(app)

    with app.app_context():
        # Ordem importa: create_all primeiro, migrate colunas, depois seed admin
        from .extensions import db as _db
        _db.create_all()
        _run_migrations(app)
        _init_db(app)

    return app


def _configure_logging(app: Flask) -> None:
    level = logging.DEBUG if app.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    app.logger.setLevel(level)


def _configure_security_headers(app: Flask) -> None:
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Permite scripts inline (necessário para os templates da app)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "connect-src 'self';"
        )
        if not app.debug:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


def _run_migrations(app: Flask) -> None:
    """Aplica novas colunas em tabelas existentes sem Alembic (SQLite safe)."""
    from sqlalchemy import text

    migrations = [
        # tabela, coluna, SQL
        ("user",       "profile_nome",       "ALTER TABLE user ADD COLUMN profile_nome VARCHAR(120)"),
        ("user",       "profile_escritorio", "ALTER TABLE user ADD COLUMN profile_escritorio VARCHAR(120)"),
        ("user",       "profile_cargo",      "ALTER TABLE user ADD COLUMN profile_cargo VARCHAR(80)"),
        ("user",       "trial_warned_at",    "ALTER TABLE user ADD COLUMN trial_warned_at DATETIME"),
        ("generation", "feedback",           "ALTER TABLE generation ADD COLUMN feedback BOOLEAN"),
    ]

    with db.engine.connect() as conn:
        for table, column, sql in migrations:
            try:
                result = conn.execute(text(f"PRAGMA table_info({table})"))
                existing = {row[1] for row in result}
                if column not in existing:
                    conn.execute(text(sql))
                    conn.commit()
                    app.logger.info(f"Migração: adicionada coluna {table}.{column}")
            except Exception as e:
                app.logger.warning(f"Migração ignorada ({table}.{column}): {e}")


def _init_db(app: Flask) -> None:
    from .models import User, Generation
    from werkzeug.security import generate_password_hash

    admin_email = app.config.get("ADMIN_EMAIL", "admin@contaia.com.br")
    admin_pwd = app.config.get("ADMIN_PASSWORD")

    if not admin_pwd:
        app.logger.warning(
            "ADMIN_PASSWORD não definida — conta admin não será criada automaticamente."
        )
        return

    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            name="Administrador",
            email=admin_email,
            password_hash=generate_password_hash(admin_pwd),
            plan="active",
            is_admin=True,
        )
        db.session.add(admin)
        db.session.commit()
        app.logger.info(f"Conta admin criada: {admin_email}")
