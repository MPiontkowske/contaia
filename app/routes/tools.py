import json
from flask import Blueprint, render_template, session
from ..extensions import db
from ..models import User, Generation, Template
from ..decorators import access_required

tools_bp = Blueprint("tools", __name__)


def _recent_for_tool(user_id: int, category: str, limit: int = 5):
    from ..models import TOOL_CATEGORY
    tool_keys = [k for k, v in TOOL_CATEGORY.items() if v == category]
    return (
        Generation.query
        .filter_by(user_id=user_id)
        .filter(Generation.tool.in_(tool_keys))
        .order_by(Generation.created_at.desc())
        .limit(limit)
        .all()
    )


def _templates_for_category(user_id: int, category: str) -> str:
    """Retorna templates da categoria como JSON string para uso no template."""
    items = (
        Template.query
        .filter_by(user_id=user_id)
        .filter(Template.tool.like(f"{category}_%"))
        .order_by(Template.created_at.desc())
        .limit(50)
        .all()
    )
    return json.dumps([t.to_dict() for t in items], ensure_ascii=False)


@tools_bp.route("/ferramenta/cobranca")
@access_required
def tool_cobranca():
    user = db.session.get(User, session["user_id"])
    recentes = _recent_for_tool(user.id, "cobranca")
    templates_json = _templates_for_category(user.id, "cobranca")
    return render_template("tool_cobranca.html", user=user, recentes=recentes,
                           templates_json=templates_json)


@tools_bp.route("/ferramenta/relatorio")
@access_required
def tool_relatorio():
    user = db.session.get(User, session["user_id"])
    recentes = _recent_for_tool(user.id, "relatorio")
    templates_json = _templates_for_category(user.id, "relatorio")
    return render_template("tool_relatorio.html", user=user, recentes=recentes,
                           templates_json=templates_json)


@tools_bp.route("/ferramenta/receita")
@access_required
def tool_receita():
    user = db.session.get(User, session["user_id"])
    recentes = _recent_for_tool(user.id, "receita")
    templates_json = _templates_for_category(user.id, "receita")
    return render_template("tool_receita.html", user=user, recentes=recentes,
                           templates_json=templates_json)
