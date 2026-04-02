import secrets
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from ..extensions import db, limiter
from ..models import User

auth_bp = Blueprint("auth", __name__)


def _maybe_send_trial_warning(user) -> None:
    """Dispara o e-mail D-2 ao fazer login, uma única vez."""
    days = user.trial_days_remaining
    if days is None or days > 2 or user.trial_warned_at is not None:
        return
    # Marca antes de enviar para evitar reenvio em logins simultâneos
    user.trial_warned_at = datetime.utcnow()
    db.session.flush()
    from ..services.email import send_trial_expiry_warning
    send_trial_expiry_warning(user)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("15 per minute", methods=["POST"])
def login():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        email = data.get("email", "").strip().lower()
        pwd = data.get("password", "")

        if not email or not pwd:
            return jsonify({"error": "Preencha e-mail e senha."}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, pwd):
            return jsonify({"error": "E-mail ou senha incorretos."}), 401

        session.permanent = True
        session["user_id"] = user.id

        user.last_login_at = datetime.utcnow()
        _maybe_send_trial_warning(user)
        db.session.commit()

        return jsonify({"ok": True, "admin": user.is_admin})

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def register():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        pwd = data.get("password", "")

        if not name or not email or not pwd:
            return jsonify({"error": "Preencha todos os campos."}), 400
        if len(name) < 2:
            return jsonify({"error": "Nome deve ter ao menos 2 caracteres."}), 400
        if len(pwd) < 6:
            return jsonify({"error": "Senha deve ter ao menos 6 caracteres."}), 400
        if "@" not in email or "." not in email.split("@")[-1]:
            return jsonify({"error": "E-mail inválido."}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "E-mail já cadastrado."}), 400

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(pwd),
        )
        db.session.add(user)
        db.session.commit()

        session.permanent = True
        session["user_id"] = user.id

        from ..services.email import send_welcome
        send_welcome(user)

        return jsonify({"ok": True})

    return render_template("register.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@auth_bp.route("/esqueci-senha", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def esqueci_senha():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        email = data.get("email", "").strip().lower()
        if not email:
            return jsonify({"error": "Informe o e-mail."}), 400

        user = User.query.filter_by(email=email).first()
        # Sempre retorna OK para não revelar se o e-mail existe
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expires = datetime.utcnow() + timedelta(hours=2)
            db.session.commit()
            from ..services.email import send_password_reset
            send_password_reset(user, token)

        return jsonify({"ok": True})

    return render_template("esqueci_senha.html")


@auth_bp.route("/redefinir-senha/<token>", methods=["GET", "POST"])
def redefinir_senha(token):
    user = User.query.filter_by(reset_token=token).first()
    token_invalido = not user or (
        user.reset_token_expires and user.reset_token_expires < datetime.utcnow()
    )

    if request.method == "POST":
        if token_invalido:
            return jsonify({"error": "Link expirado ou inválido."}), 400
        data = request.get_json(silent=True) or {}
        nova_senha = data.get("password", "")
        if len(nova_senha) < 6:
            return jsonify({"error": "Senha deve ter ao menos 6 caracteres."}), 400
        user.password_hash = generate_password_hash(nova_senha)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        return jsonify({"ok": True})

    return render_template("redefinir_senha.html", token_invalido=token_invalido, token=token)


@auth_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))
