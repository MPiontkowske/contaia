import os
from datetime import timedelta


class Config:
    # --- Segurança ---
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_NAME = "contaia_session"
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)

    # --- Banco de dados ---
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///contaia.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- IA ---
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

    # --- Admin ---
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@contaia.com.br")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

    # --- Rate limiting ---
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_DEFAULT = "500 per day"

    # --- E-mail (Flask-Mail) ---
    MAIL_SERVER   = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT     = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS  = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER", "ContaIA <noreply@contaia.com.br>"
    )

    # --- Monitoramento ---
    SENTRY_DSN = os.environ.get("SENTRY_DSN")

    # --- Produto ---
    TRIAL_DAYS = 7
    PLAN_PRICE_BRL = 97
    WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "5511999999999")


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    @classmethod
    def validate(cls):
        missing = []
        if not cls.SECRET_KEY:
            missing.append("SECRET_KEY")
        if not cls.ANTHROPIC_API_KEY:
            missing.append("ANTHROPIC_API_KEY")
        if not cls.ADMIN_PASSWORD:
            missing.append("ADMIN_PASSWORD")
        if missing:
            raise RuntimeError(
                f"Variáveis de ambiente obrigatórias não definidas: {', '.join(missing)}"
            )


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
