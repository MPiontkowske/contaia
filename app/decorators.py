from functools import wraps
from flask import session, redirect, url_for, jsonify, request
from .models import User
from .extensions import db


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json:
                return jsonify({"error": "Não autenticado."}), 401
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        user = db.session.get(User, session["user_id"])
        if not user or not user.is_admin:
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)
    return decorated


def access_required(f):
    """Requer login + plano ativo (trial válido ou assinatura)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json:
                return jsonify({"error": "Não autenticado."}), 401
            return redirect(url_for("auth.login"))
        user = db.session.get(User, session["user_id"])
        if not user:
            session.clear()
            return redirect(url_for("auth.login"))
        if not user.has_access:
            if request.is_json:
                return jsonify({"error": "Acesso encerrado. Assine para continuar."}), 403
            return redirect(url_for("main.sem_acesso"))
        return f(*args, **kwargs)
    return decorated
