import json
import logging
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db, limiter
from ..models import User, Generation, Template
from ..decorators import login_required, access_required
from ..services.ai import call_claude
from ..services.prompts import build_prompt, auto_title, TOOLS

logger = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/gerar", methods=["POST"])
@access_required
@limiter.limit("40 per hour")
def api_gerar():
    user = db.session.get(User, session["user_id"])
    data = request.get_json(silent=True) or {}

    tool = data.get("tool", "").strip()
    campos = data.get("campos", {})

    if not isinstance(campos, dict):
        return jsonify({"error": "Dados inválidos."}), 400
    if tool not in TOOLS:
        return jsonify({"error": "Ferramenta inválida."}), 400

    try:
        system_prompt, user_message, max_tokens, model = build_prompt(tool, campos)
        resultado = call_claude(system_prompt, user_message, max_tokens, model)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception:
        logger.exception(f"Erro inesperado em api_gerar (tool={tool}, user={user.id})")
        return jsonify({"error": "Erro interno. Tente novamente."}), 500

    titulo = auto_title(tool, campos)
    gen = Generation(
        user_id=user.id,
        tool=tool,
        titulo=titulo,
        campos_json=json.dumps(campos, ensure_ascii=False),
        resultado=resultado,
    )
    db.session.add(gen)
    db.session.commit()

    return jsonify({"resultado": resultado, "id": gen.id})


@api_bp.route("/favoritar/<int:gen_id>", methods=["POST"])
@login_required
def api_favoritar(gen_id: int):
    user_id = session["user_id"]
    gen = Generation.query.filter_by(id=gen_id, user_id=user_id).first_or_404()
    gen.is_favorite = not gen.is_favorite
    db.session.commit()
    return jsonify({"ok": True, "is_favorite": gen.is_favorite})


@api_bp.route("/deletar/<int:gen_id>", methods=["DELETE"])
@login_required
def api_deletar(gen_id: int):
    user_id = session["user_id"]
    gen = Generation.query.filter_by(id=gen_id, user_id=user_id).first_or_404()
    db.session.delete(gen)
    db.session.commit()
    return jsonify({"ok": True})


@api_bp.route("/historico-recente", methods=["GET"])
@login_required
def api_historico_recente():
    user_id = session["user_id"]
    tool_filter = request.args.get("tool", "")
    q = Generation.query.filter_by(user_id=user_id)
    if tool_filter:
        q = q.filter_by(tool=tool_filter)
    items = q.order_by(Generation.created_at.desc()).limit(10).all()
    return jsonify([g.to_dict() for g in items])


# ── Perfil do contador ────────────────────────────────────────────────────────

@api_bp.route("/perfil", methods=["GET", "POST"])
@login_required
def api_perfil():
    user = db.session.get(User, session["user_id"])

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        name = data.get("name", "").strip()
        if name:
            user.name = name[:120]
        for field in ("profile_nome", "profile_escritorio", "profile_cargo"):
            limits = {"profile_nome": 120, "profile_escritorio": 120, "profile_cargo": 80}
            if field in data:
                val = data[field].strip()
                setattr(user, field, val[:limits[field]] if val else None)
        db.session.commit()
        return jsonify({"ok": True})

    return jsonify({
        "name": user.name,
        "email": user.email,
        "profile_nome": user.profile_nome or "",
        "profile_escritorio": user.profile_escritorio or "",
        "profile_cargo": user.profile_cargo or "",
    })


@api_bp.route("/alterar-senha", methods=["POST"])
@login_required
@limiter.limit("10 per hour")
def api_alterar_senha():
    user = db.session.get(User, session["user_id"])
    data = request.get_json(silent=True) or {}
    atual = data.get("senha_atual", "")
    nova = data.get("nova_senha", "")

    if not check_password_hash(user.password_hash, atual):
        return jsonify({"error": "Senha atual incorreta."}), 400
    if len(nova) < 6:
        return jsonify({"error": "Nova senha deve ter ao menos 6 caracteres."}), 400

    user.password_hash = generate_password_hash(nova)
    db.session.commit()
    return jsonify({"ok": True})


# ── Templates reutilizáveis ───────────────────────────────────────────────────

@api_bp.route("/templates", methods=["GET"])
@login_required
def api_templates_list():
    user_id = session["user_id"]
    category = request.args.get("category", "")
    q = Template.query.filter_by(user_id=user_id)
    if category:
        # filtra por prefixo da categoria (ex: "cobranca_")
        q = q.filter(Template.tool.like(f"{category}_%"))
    items = q.order_by(Template.created_at.desc()).limit(50).all()
    return jsonify([t.to_dict() for t in items])


@api_bp.route("/templates", methods=["POST"])
@login_required
@limiter.limit("200 per day")
def api_templates_save():
    user_id = session["user_id"]
    data = request.get_json(silent=True) or {}
    tool = data.get("tool", "").strip()
    nome = data.get("nome", "").strip()[:120]
    campos = data.get("campos", {})

    if not tool or not nome:
        return jsonify({"error": "Nome e ferramenta são obrigatórios."}), 400
    if tool not in TOOLS:
        return jsonify({"error": "Ferramenta inválida."}), 400
    if not isinstance(campos, dict):
        return jsonify({"error": "Campos inválidos."}), 400

    tmpl = Template(
        user_id=user_id,
        tool=tool,
        nome=nome,
        campos_json=json.dumps(campos, ensure_ascii=False),
    )
    db.session.add(tmpl)
    db.session.commit()
    return jsonify({"ok": True, "id": tmpl.id, "nome": tmpl.nome})


@api_bp.route("/templates/<int:tmpl_id>", methods=["DELETE"])
@login_required
def api_templates_delete(tmpl_id: int):
    user_id = session["user_id"]
    tmpl = Template.query.filter_by(id=tmpl_id, user_id=user_id).first_or_404()
    db.session.delete(tmpl)
    db.session.commit()
    return jsonify({"ok": True})


# ── Feedback ─────────────────────────────────────────────────────────────────

@api_bp.route("/feedback/<int:gen_id>", methods=["POST"])
@login_required
def api_feedback(gen_id: int):
    user_id = session["user_id"]
    gen = Generation.query.filter_by(id=gen_id, user_id=user_id).first_or_404()
    data = request.get_json(silent=True) or {}
    value = data.get("value")
    if value not in (True, False):
        return jsonify({"error": "Valor inválido."}), 400
    gen.feedback = value
    db.session.commit()
    return jsonify({"ok": True})
