from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()


def _get_user_key():
    from flask import session
    uid = session.get("user_id")
    if uid:
        return f"user:{uid}"
    return get_remote_address()


limiter = Limiter(
    key_func=_get_user_key,
    storage_uri="memory://",
    default_limits=["500 per day"],
)
