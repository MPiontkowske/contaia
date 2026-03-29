from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from ..extensions import db, limiter
from ..models import User

auth_bp = Blueprint("auth", __name__)


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
        return jsonify({"ok": True})

    return render_template("register.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@auth_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))
