import time
import logging
from flask import Blueprint, jsonify, render_template_string

health_bp = Blueprint("health", __name__)
log = logging.getLogger(__name__)

_STATUS_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>ContaIA — Status</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{background:#09090f;color:#e8e8e0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px}
    .card{background:#111118;border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:36px 32px;max-width:420px;width:100%}
    .logo{font-size:1.4rem;font-weight:700;margin-bottom:28px}
    .logo span{color:#d4a843}
    h1{font-size:1rem;font-weight:600;margin-bottom:20px;color:#888}
    .item{display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05)}
    .item:last-child{border-bottom:none}
    .item-name{font-size:.9rem}
    .badge{font-size:.75rem;font-weight:700;padding:3px 10px;border-radius:20px}
    .ok{background:rgba(34,197,94,.15);color:#22c55e}
    .fail{background:rgba(239,68,68,.15);color:#ef4444}
    .overall{margin-top:24px;text-align:center;font-size:.85rem;color:#555}
    .ts{margin-top:6px;font-size:.72rem;color:#444}
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">Conta<span>IA</span></div>
    <h1>Status dos serviços</h1>
    {% for item in checks %}
    <div class="item">
      <span class="item-name">{{ item.name }}</span>
      <span class="badge {{ 'ok' if item.ok else 'fail' }}">{{ 'Operacional' if item.ok else 'Falha' }}</span>
    </div>
    {% endfor %}
    <div class="overall">
      {% if all_ok %}Todos os sistemas operacionais{% else %}Degradação parcial — verifique os logs{% endif %}
    </div>
    <div class="ts">Verificado em {{ ts }}</div>
  </div>
</body>
</html>"""


def _check_db():
    try:
        from ..extensions import db
        db.session.execute(db.text("SELECT 1"))
        return True
    except Exception as e:
        log.warning("Health DB falhou: %s", e)
        return False


def _check_redis():
    try:
        from ..celery_app import get_celery
        celery = get_celery()
        if celery is None:
            return None  # Redis não configurado — não é falha
        conn = celery.backend.client
        conn.ping()
        return True
    except Exception as e:
        log.warning("Health Redis falhou: %s", e)
        return False


def _check_worker():
    try:
        from ..celery_app import get_celery
        celery = get_celery()
        if celery is None:
            return None  # Celery não configurado
        inspect = celery.control.inspect(timeout=1.5)
        active = inspect.active()
        return active is not None
    except Exception as e:
        log.warning("Health Worker falhou: %s", e)
        return False


@health_bp.route("/health")
def health():
    t0 = time.monotonic()

    db_ok = _check_db()
    redis_ok = _check_redis()
    worker_ok = _check_worker()

    checks = {"database": db_ok}
    if redis_ok is not None:
        checks["redis"] = redis_ok
    if worker_ok is not None:
        checks["worker"] = worker_ok

    all_ok = all(checks.values())
    status_code = 200 if all_ok else 503

    return jsonify({
        "status": "ok" if all_ok else "degraded",
        "checks": checks,
        "latency_ms": round((time.monotonic() - t0) * 1000, 1),
    }), status_code


@health_bp.route("/status")
def status_page():
    from datetime import datetime

    db_ok = _check_db()
    redis_ok = _check_redis()
    worker_ok = _check_worker()

    checks = [{"name": "Banco de dados", "ok": db_ok}]
    if redis_ok is not None:
        checks.append({"name": "Redis / Fila", "ok": redis_ok})
    if worker_ok is not None:
        checks.append({"name": "Worker Celery", "ok": worker_ok})

    all_ok = all(c["ok"] for c in checks)
    ts = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")

    return render_template_string(_STATUS_HTML, checks=checks, all_ok=all_ok, ts=ts)
