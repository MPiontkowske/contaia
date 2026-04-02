from flask import Blueprint, render_template, session, redirect, url_for, request
from datetime import datetime
from ..extensions import db
from ..models import User, Generation
from ..decorators import login_required

main_bp = Blueprint("main", __name__)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    user = db.session.get(User, session["user_id"])
    recentes = (
        Generation.query
        .filter_by(user_id=user.id)
        .order_by(Generation.created_at.desc())
        .limit(8)
        .all()
    )
    total = Generation.query.filter_by(user_id=user.id).count()
    favoritos = Generation.query.filter_by(user_id=user.id, is_favorite=True).count()
    return render_template(
        "dashboard.html",
        user=user,
        recentes=recentes,
        total=total,
        favoritos=favoritos,
    )


@main_bp.route("/historico")
@login_required
def historico():
    user = db.session.get(User, session["user_id"])
    categoria = request.args.get("categoria", "")
    page = request.args.get("page", 1, type=int)

    busca = request.args.get("q", "").strip()
    query = Generation.query.filter_by(user_id=user.id)

    from ..models import TOOL_CATEGORY
    if categoria:
        valid_tools = [k for k, v in TOOL_CATEGORY.items() if v == categoria]
        query = query.filter(Generation.tool.in_(valid_tools))

    if busca:
        termo = f"%{busca}%"
        query = query.filter(
            db.or_(
                Generation.titulo.ilike(termo),
                Generation.resultado.ilike(termo),
            )
        )

    paginacao = query.order_by(Generation.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template(
        "historico.html",
        user=user,
        paginacao=paginacao,
        categoria=categoria,
        busca=busca,
    )


@main_bp.route("/sem-acesso")
@login_required
def sem_acesso():
    user = db.session.get(User, session["user_id"])
    return render_template("sem_acesso.html", user=user)


@main_bp.route("/perfil")
@login_required
def perfil():
    user = db.session.get(User, session["user_id"])
    return render_template("perfil.html", user=user)


@main_bp.route("/planos")
@login_required
def planos():
    from flask import current_app
    user = db.session.get(User, session["user_id"])
    whatsapp = current_app.config.get("WHATSAPP_NUMBER", "5511999999999")
    return render_template("planos.html", user=user, whatsapp=whatsapp)
