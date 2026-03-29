from flask import Blueprint, render_template, jsonify
from ..extensions import db
from ..models import User, Generation
from ..decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@admin_required
def admin_dashboard():
    users = User.query.order_by(User.created_at.desc()).all()
    total_geracoes = Generation.query.count()
    active_count = User.query.filter_by(plan="active").count()
    trial_count = User.query.filter_by(plan="trial").count()
    cancelled_count = User.query.filter_by(plan="cancelled").count()
    return render_template(
        "admin.html",
        users=users,
        total_geracoes=total_geracoes,
        active=active_count,
        trial=trial_count,
        cancelled=cancelled_count,
    )


@admin_bp.route("/toggle-plan/<int:user_id>", methods=["POST"])
@admin_required
def toggle_plan(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado."}), 404
    if user.is_admin:
        return jsonify({"error": "Não é possível alterar plano do administrador."}), 400
    user.plan = "active" if user.plan != "active" else "cancelled"
    db.session.commit()
    return jsonify({"ok": True, "plan": user.plan})
