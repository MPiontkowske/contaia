from flask import Blueprint, render_template, session, redirect, url_for, request
from datetime import datetime, timedelta
from ..extensions import db
from ..models import User, Generation, TOOL_CATEGORY
from ..decorators import login_required

main_bp = Blueprint("main", __name__)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    from flask import current_app
    from sqlalchemy import func
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
    trial_limit = current_app.config.get("TRIAL_GENERATION_LIMIT", 20)

    # Atividade dos últimos 14 dias
    hoje = datetime.utcnow().date()
    inicio = hoje - timedelta(days=13)
    rows = (
        db.session.query(func.date(Generation.created_at), func.count(Generation.id))
        .filter(Generation.user_id == user.id, Generation.created_at >= inicio)
        .group_by(func.date(Generation.created_at))
        .all()
    )
    ativ_map = {str(r[0]): r[1] for r in rows}
    ativ_labels = [(inicio + timedelta(days=i)).strftime("%d/%m") for i in range(14)]
    ativ_dates  = [(inicio + timedelta(days=i)).isoformat() for i in range(14)]
    ativ_data   = [ativ_map.get(d, 0) for d in ativ_dates]

    # Breakdown por categoria
    cat_rows = (
        db.session.query(Generation.tool, func.count(Generation.id))
        .filter_by(user_id=user.id)
        .group_by(Generation.tool)
        .all()
    )
    cat_totals = {"cobranca": 0, "relatorio": 0, "receita": 0, "cliente": 0}
    for tool, cnt in cat_rows:
        cat = TOOL_CATEGORY.get(tool, "")
        if cat in cat_totals:
            cat_totals[cat] += cnt

    return render_template(
        "dashboard.html",
        user=user,
        recentes=recentes,
        total=total,
        favoritos=favoritos,
        trial_limit=trial_limit,
        ativ_labels=ativ_labels,
        ativ_data=ativ_data,
        cat_totals=cat_totals,
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


@main_bp.route("/favoritos")
@login_required
def favoritos():
    user = db.session.get(User, session["user_id"])
    categoria = request.args.get("categoria", "")
    from ..models import TOOL_CATEGORY
    query = Generation.query.filter_by(user_id=user.id, is_favorite=True)
    if categoria:
        valid_tools = [k for k, v in TOOL_CATEGORY.items() if v == categoria]
        query = query.filter(Generation.tool.in_(valid_tools))
    items = query.order_by(Generation.created_at.desc()).all()
    return render_template("favoritos.html", user=user, items=items, categoria=categoria)


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
