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
    # Corrige prefixo legado "postgres://" → "postgresql://" (SQLAlchemy 2.x)
    _db_url = os.environ.get("DATABASE_URL", "sqlite:///contaia.db")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
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
    TRIAL_GENERATION_LIMIT = int(os.environ.get("TRIAL_GENERATION_LIMIT", 20))
    PLAN_PRICE_BRL = 97
    WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "5511999999999")

    # --- Pagar.me ---
    PAGARME_WEBHOOK_SECRET = os.environ.get("PAGARME_WEBHOOK_SECRET")
    # Link de pagamento pré-configurado no painel Pagar.me (substitui o WhatsApp)
    PAGARME_PAYMENT_LINK = os.environ.get("PAGARME_PAYMENT_LINK")

    # --- Celery / Redis ---
    # Se não definido, a geração continua síncrona (sem Celery)
    CELERY_BROKER_URL    = os.environ.get("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND")


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    # Mude para True apenas quando usar HTTPS
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
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
