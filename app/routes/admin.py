from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, session
from sqlalchemy import func
from ..extensions import db
from ..models import User, Generation
from ..decorators import admin_required

_SUBSCRIPTION_DAYS = 30

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@admin_required
def admin_dashboard():
    current_user = db.session.get(User, session["user_id"])
    users = User.query.order_by(User.created_at.desc()).all()
    total_geracoes = Generation.query.count()
    active_count = User.query.filter_by(plan="active").count()
    trial_count = User.query.filter_by(plan="trial").count()
    cancelled_count = User.query.filter_by(plan="cancelled").count()

    # Novos usuários por dia — últimas 4 semanas
    hoje = datetime.utcnow().date()
    inicio = hoje - timedelta(days=27)
    rows = (
        db.session.query(func.date(User.created_at), func.count(User.id))
        .filter(User.created_at >= inicio)
        .group_by(func.date(User.created_at))
        .all()
    )
    cadastros_map = {str(r[0]): r[1] for r in rows}
    chart_labels = [(inicio + timedelta(days=i)).strftime("%d/%m") for i in range(28)]
    chart_dates  = [(inicio + timedelta(days=i)).isoformat() for i in range(28)]
    chart_data   = [cadastros_map.get(d, 0) for d in chart_dates]

    # Assinaturas vencendo em até 7 dias
    soon = datetime.utcnow() + timedelta(days=7)
    expiring_soon = (
        User.query
        .filter(
            User.plan == "active",
            User.subscription_end.isnot(None),
            User.subscription_end <= soon,
        )
        .order_by(User.subscription_end)
        .all()
    )

    return render_template(
        "admin.html",
        user=current_user,
        users=users,
        total_geracoes=total_geracoes,
        active=active_count,
        trial=trial_count,
        cancelled=cancelled_count,
        chart_labels=chart_labels,
        chart_data=chart_data,
        expiring_soon=expiring_soon,
    )


@admin_bp.route("/toggle-plan/<int:user_id>", methods=["POST"])
@admin_required
def toggle_plan(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado."}), 404
    if user.is_admin:
        return jsonify({"error": "Não é possível alterar plano do administrador."}), 400
    if user.plan != "active":
        user.plan = "active"
        user.subscription_end = datetime.utcnow() + timedelta(days=_SUBSCRIPTION_DAYS)
        user.subscription_warned_at = None  # reset para próximo ciclo
    else:
        user.plan = "cancelled"
        user.subscription_end = None
    db.session.commit()
    sub_end = user.subscription_end.strftime("%d/%m/%Y") if user.subscription_end else None
    return jsonify({"ok": True, "plan": user.plan, "subscription_end": sub_end})
