import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, redirect, current_app
from ..extensions import db
from ..models import User
from ..decorators import login_required

logger = logging.getLogger(__name__)
pagarme_bp = Blueprint("pagarme", __name__)

_SUBSCRIPTION_DAYS = 30


def _valid_signature(body: bytes, signature: str, secret: str) -> bool:
    """Valida a assinatura HMAC-SHA256 enviada pelo Pagar.me."""
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@pagarme_bp.route("/checkout")
@login_required
def checkout():
    """Redireciona para o link de pagamento Pagar.me pré-configurado."""
    link = current_app.config.get("PAGARME_PAYMENT_LINK")
    if not link:
        return redirect("/planos")
    return redirect(link)


@pagarme_bp.route("/webhook/pagarme", methods=["POST"])
def webhook():
    """
    Recebe eventos do Pagar.me e atualiza o plano do usuário.

    Eventos tratados:
    - subscription.payment_succeeded / order.paid → ativa plano por 30 dias
    - subscription.canceled                        → cancela plano
    - subscription.payment_failed                  → loga, admin intervém

    O usuário é identificado pelo e-mail presente em data.customer.email
    ou em data.metadata.user_email.
    """
    secret = current_app.config.get("PAGARME_WEBHOOK_SECRET", "")
    raw = request.get_data()
    sig = request.headers.get("x-pagarme-signature", "")

    if secret and not _valid_signature(raw, sig, secret):
        logger.warning("Pagar.me webhook: assinatura inválida")
        return jsonify({"error": "invalid signature"}), 401

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return jsonify({"error": "invalid json"}), 400

    event = data.get("type", "")
    logger.info("Pagar.me webhook recebido: %s", event)

    # Localizar e-mail do assinante
    payload = data.get("data") or {}
    customer = payload.get("customer") or {}
    email = (customer.get("email") or "").strip().lower()

    if not email:
        meta = payload.get("metadata") or {}
        email = (meta.get("user_email") or "").strip().lower()

    if not email:
        logger.warning("Pagar.me webhook %s: sem e-mail no payload", event)
        return jsonify({"ok": True})  # 200 para evitar retry desnecessário

    user = User.query.filter_by(email=email).first()
    if not user:
        logger.warning("Pagar.me webhook %s: usuário não encontrado (%s)", event, email)
        return jsonify({"ok": True})

    if event in ("subscription.payment_succeeded", "order.paid"):
        user.plan = "active"
        user.subscription_end = datetime.utcnow() + timedelta(days=_SUBSCRIPTION_DAYS)
        user.subscription_warned_at = None  # reset para próximo ciclo de aviso
        db.session.commit()
        logger.info("Pagar.me: plano ativado para %s até %s", email, user.subscription_end)

    elif event == "subscription.canceled":
        user.plan = "cancelled"
        user.subscription_end = None
        db.session.commit()
        logger.info("Pagar.me: assinatura cancelada para %s", email)

    elif event == "subscription.payment_failed":
        # Mantém ativo por ora — admin pode intervir; apenas loga
        logger.warning("Pagar.me: falha de pagamento para %s (plano mantido)", email)

    return jsonify({"ok": True})
